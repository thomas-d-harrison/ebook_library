import sqlite3
import csv
from pathlib import Path
from datetime import datetime

class StoryGraphImporter:
    def __init__(self, db_path='tt_db_ebook_lib.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"Connected to database: {self.db_path}")
    
    def create_reading_tables(self):
        """Create tables for reading history data"""
        
        # Reading history table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                title TEXT,
                authors TEXT,
                isbn TEXT,
                format TEXT,
                read_status TEXT,
                date_added TEXT,
                last_date_read TEXT,
                dates_read TEXT,
                read_count INTEGER DEFAULT 0,
                star_rating REAL,
                review TEXT,
                owned TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        ''')
        
        # Book attributes table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_history_id INTEGER,
                moods TEXT,
                pace TEXT,
                character_or_plot TEXT,
                strong_character_dev TEXT,
                loveable_characters TEXT,
                diverse_characters TEXT,
                flawed_characters TEXT,
                FOREIGN KEY (reading_history_id) REFERENCES reading_history (id) ON DELETE CASCADE
            )
        ''')
        
        # Content warnings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_history_id INTEGER,
                warning_text TEXT,
                warning_description TEXT,
                FOREIGN KEY (reading_history_id) REFERENCES reading_history (id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
        print("Reading history tables created successfully")
    
    def match_book_by_title_author(self, title, authors):
        """Try to match StoryGraph book to existing book in library"""
        # Clean up title and authors
        title_clean = title.strip().lower()
        authors_clean = authors.strip().lower() if authors else ''
        
        # Try exact match first
        self.cursor.execute('''
            SELECT b.id 
            FROM books b
            JOIN book_authors ba ON b.id = ba.book_id
            JOIN authors a ON ba.author_id = a.id
            WHERE LOWER(b.title) = ? AND LOWER(a.author_name) = ?
            LIMIT 1
        ''', (title_clean, authors_clean))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        # Try title-only match
        self.cursor.execute('''
            SELECT id FROM books 
            WHERE LOWER(title) = ?
            LIMIT 1
        ''', (title_clean,))
        
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def import_storygraph_csv(self, csv_path):
        """Import StoryGraph CSV data"""
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            return
        
        imported = 0
        matched = 0
        print(csv_path, csv_path.exists())
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                title = row.get('Title', '')
                authors = row.get('Authors', '')
                
                # Try to match with existing book
                book_id = self.match_book_by_title_author(title, authors)
                if book_id:
                    matched += 1
                
                # Insert reading history
                self.cursor.execute('''
                    INSERT INTO reading_history (
                        book_id, title, authors, isbn, format, read_status,
                        date_added, last_date_read, dates_read, read_count,
                        star_rating, review, owned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    book_id,
                    title,
                    authors,
                    row.get('ISBN/UID', ''),
                    row.get('Format', ''),
                    row.get('Read Status', ''),
                    row.get('Date Added', ''),
                    row.get('Last Date Read', ''),
                    row.get('Dates Read', ''),
                    int(row.get('Read Count', 0)) if row.get('Read Count') else 0,
                    float(row.get('Star Rating', 0)) if row.get('Star Rating') else None,
                    row.get('Review', ''),
                    row.get('Owned?', '')
                ))
                
                reading_history_id = self.cursor.lastrowid
                
                # Insert book attributes
                self.cursor.execute('''
                    INSERT INTO book_attributes (
                        reading_history_id, moods, pace, character_or_plot,
                        strong_character_dev, loveable_characters, 
                        diverse_characters, flawed_characters
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reading_history_id,
                    row.get('Moods', ''),
                    row.get('Pace', ''),
                    row.get('Character- or Plot-Driven?', ''),
                    row.get('Strong Character Development?', ''),
                    row.get('Loveable Characters?', ''),
                    row.get('Diverse Characters?', ''),
                    row.get('Flawed Characters?', '')
                ))
                
                # Insert content warnings if present
                warnings = row.get('Content Warnings', '')
                if warnings:
                    self.cursor.execute('''
                        INSERT INTO content_warnings (
                            reading_history_id, warning_text, warning_description
                        ) VALUES (?, ?, ?)
                    ''', (
                        reading_history_id,
                        warnings,
                        row.get('Content Warning Description', '')
                    ))
                
                imported += 1
                
                if imported % 50 == 0:
                    print(f"Imported {imported} books...")
        
        self.conn.commit()
        print(f"\n{'='*60}")
        print(f"Import complete!")
        print(f"Total books imported: {imported}")
        print(f"Matched to library: {matched}")
        print(f"New books: {imported - matched}")
        print(f"{'='*60}")
    
    def get_reading_stats(self):
        """Get reading statistics"""
        stats = {}
        
        # Total books read
        self.cursor.execute("SELECT COUNT(*) FROM reading_history WHERE read_status = 'read'")
        stats['books_read'] = self.cursor.fetchone()[0]
        
        # Currently reading
        self.cursor.execute("SELECT COUNT(*) FROM reading_history WHERE read_status = 'currently-reading'")
        stats['currently_reading'] = self.cursor.fetchone()[0]
        
        # To read
        self.cursor.execute("SELECT COUNT(*) FROM reading_history WHERE read_status = 'to-read'")
        stats['to_read'] = self.cursor.fetchone()[0]
        
        # Average rating
        self.cursor.execute("SELECT AVG(star_rating) FROM reading_history WHERE star_rating IS NOT NULL")
        avg_rating = self.cursor.fetchone()[0]
        stats['avg_rating'] = round(avg_rating, 2) if avg_rating else 0
        
        # Top rated books
        self.cursor.execute('''
            SELECT title, authors, star_rating 
            FROM reading_history 
            WHERE star_rating IS NOT NULL 
            ORDER BY star_rating DESC 
            LIMIT 5
        ''')
        stats['top_rated'] = self.cursor.fetchall()
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")

def main():
    print("="*60)
    print("StoryGraph Reading History Importer")
    print("="*60)
    
    # Initialize importer
    importer = StoryGraphImporter()
    importer.connect()
    
    # Create tables
    importer.create_reading_tables()
    
    # Import CSV (use the actual file name)
    csv_path = Path(__file__).parent / 'tt storygraph data.csv'
    print(f"\nImporting from: {csv_path}")

    importer.import_storygraph_csv(csv_path)

    
    # Show stats
    print("\n" + "="*60)
    print("READING STATISTICS")
    print("="*60)
    stats = importer.get_reading_stats()
    print(f"Books Read: {stats['books_read']}")
    print(f"Currently Reading: {stats['currently_reading']}")
    print(f"To Read: {stats['to_read']}")
    print(f"Average Rating: {stats['avg_rating']} ⭐")
    
    if stats['top_rated']:
        print(f"\nTop Rated Books:")
        for title, authors, rating in stats['top_rated']:
            print(f"  ⭐ {rating} - {title} by {authors}")
    
    importer.close()
    print("\nDone!")

if __name__ == "__main__":
    main()