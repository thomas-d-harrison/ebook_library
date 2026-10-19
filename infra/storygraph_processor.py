import sqlite3
import csv
import re
import difflib
import unicodedata
from pathlib import Path
from datetime import datetime


# ---- matching helpers -------------------------------------------------------
def _fold(s):
    s = unicodedata.normalize('NFKD', s or '')
    return ''.join(ch for ch in s if not unicodedata.combining(ch))

def norm_title(t):
    """Comparable title: no accents, case, 'The/A/An', (parentheticals) or :subtitle"""
    t = _fold(t).lower()
    t = re.sub(r'\([^)]*\)', '', t)
    t = t.split(':')[0]
    t = t.replace('&', ' and ').replace("'", '').replace('\u2019', '')
    t = re.sub(r'[^a-z0-9 ]', ' ', t)
    return re.sub(r'^(the|a|an) ', '', ' '.join(t.split()))

def last_name(name):
    n = re.sub(r',?\s+(jr|sr)\.?$', '', _fold(name).lower().strip())
    w = re.findall(r"[a-z']+", n)
    return w[-1] if w else ''

def author_last_names(authors):
    return [x for x in (last_name(a) for a in re.split(r',|;|&| and ', authors or '')) if x]

def authors_compatible(sg_authors, db_authors):
    """True if any StoryGraph author's last name matches a library author (spelling-tolerant).
    If StoryGraph gives no author, the title alone decides."""
    sg = author_last_names(sg_authors)
    if not sg:
        return True
    db = [last_name(a) for a in db_authors]
    return any(a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.85
               for a in sg for b in db)

class StoryGraphImporter:
    def __init__(self, db_path='data/tt_db_ebook_lib.db'):
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
        
        # De-duplication key (added after the fact, so older databases get it too)
        cols = [r[1] for r in self.cursor.execute("PRAGMA table_info(reading_history)")]
        if 'import_key' not in cols:
            self.cursor.execute("ALTER TABLE reading_history ADD COLUMN import_key TEXT")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reading_history_import_key ON reading_history(import_key)")
        # Backfill keys for rows imported before this column existed
        for rid, title, authors, isbn in self.cursor.execute(
                "SELECT id, title, authors, isbn FROM reading_history "
                "WHERE import_key IS NULL").fetchall():
            self.conn.execute("UPDATE reading_history SET import_key = ? WHERE id = ?",
                              (self.make_key(title, authors, isbn), rid))

        # `Owned?` is no longer stored: ownership comes from the v_book_ownership view
        if 'owned' in cols:
            try:
                self.cursor.execute("ALTER TABLE reading_history DROP COLUMN owned")
                print("Dropped reading_history.owned (use v_book_ownership instead)")
            except sqlite3.OperationalError as e:
                print(f"Could not drop reading_history.owned ({e}); it is now simply ignored")

        self.conn.commit()
        print("Reading history tables created successfully")

    @staticmethod
    def make_key(title, authors, isbn):
        """Identity of a StoryGraph row: ISBN/UID if present, else title + authors"""
        isbn = (isbn or '').strip().lower()
        if isbn:
            return f"isbn:{isbn}"
        return f"ta:{(title or '').strip().lower()}|{(authors or '').strip().lower()}"
    
    def build_match_index(self):
        """Load the library once so every StoryGraph row can be matched in memory"""
        self.book_authors = {}
        for bid, name in self.cursor.execute(
                "SELECT ba.book_id, a.author_name FROM book_authors ba "
                "JOIN authors a ON a.id = ba.author_id"):
            self.book_authors.setdefault(bid, []).append(name)
        self.title_index = {}
        for bid, title in self.cursor.execute("SELECT id, title FROM books"):
            self.title_index.setdefault(norm_title(title), []).append(bid)
        self.isbn_index = {}
        for bid, value in self.cursor.execute(
                "SELECT book_id, identifier_value FROM book_identifiers "
                "WHERE identifier_type = 'ISBN'"):
            self.isbn_index.setdefault(value.strip(), []).append(bid)

    def match_book(self, title, authors, isbn):
        """Link a StoryGraph row to a library book. Returns (book_id, method) or (None, None).
        1. ISBN (exact edition), 2. title (ignoring subtitle/parentheses/accents) + author"""
        key = norm_title(title)
        isbn = (isbn or '').strip()
        if isbn and isbn in self.isbn_index:
            ids = self.isbn_index[isbn]
            # two books can share an ISBN (split volumes): prefer the one whose title matches
            for bid in ids:
                if bid in self.title_index.get(key, []):
                    return bid, 'isbn'
            return ids[0], 'isbn'
        for bid in self.title_index.get(key, []):
            if authors_compatible(authors, self.book_authors.get(bid, [])):
                return bid, 'title'
        return None, None

    def import_storygraph_csv(self, csv_path):
        """Import StoryGraph CSV data"""
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            return
        
        imported = 0
        inserted = 0
        updated = 0
        matched = 0
        by_isbn = 0
        self.build_match_index()
        print(csv_path, csv_path.exists())
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                title = row.get('Title', '')
                authors = row.get('Authors', '')
                
                isbn = row.get('ISBN/UID', '')

                # Link to the library: ISBN first, then title + author
                book_id, how = self.match_book(title, authors, isbn)
                if book_id:
                    matched += 1
                    if how == 'isbn':
                        by_isbn += 1

                key = self.make_key(title, authors, isbn)
                values = (
                    book_id,
                    title,
                    authors,
                    isbn,
                    row.get('Format', ''),
                    row.get('Read Status', ''),
                    row.get('Date Added', ''),
                    row.get('Last Date Read', ''),
                    row.get('Dates Read', ''),
                    int(row.get('Read Count', 0)) if row.get('Read Count') else 0,
                    float(row.get('Star Rating', 0)) if row.get('Star Rating') else None,
                    row.get('Review', '')
                )

                # Already imported? Update it in place (status/rating may have changed
                # in a newer export) instead of inserting a duplicate.
                self.cursor.execute(
                    "SELECT id FROM reading_history WHERE import_key = ? ORDER BY id LIMIT 1", (key,))
                existing = self.cursor.fetchone()
                if existing:
                    reading_history_id = existing[0]
                    self.cursor.execute('''
                        UPDATE reading_history SET
                            book_id = ?, title = ?, authors = ?, isbn = ?, format = ?,
                            read_status = ?, date_added = ?, last_date_read = ?,
                            dates_read = ?, read_count = ?, star_rating = ?,
                            review = ?
                        WHERE id = ?
                    ''', values + (reading_history_id,))
                    # child rows are rebuilt below
                    self.cursor.execute(
                        "DELETE FROM book_attributes WHERE reading_history_id = ?", (reading_history_id,))
                    self.cursor.execute(
                        "DELETE FROM content_warnings WHERE reading_history_id = ?", (reading_history_id,))
                    updated += 1
                else:
                    self.cursor.execute('''
                        INSERT INTO reading_history (
                            book_id, title, authors, isbn, format, read_status,
                            date_added, last_date_read, dates_read, read_count,
                            star_rating, review, import_key
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', values + (key,))
                    reading_history_id = self.cursor.lastrowid
                    inserted += 1

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
        print(f"Rows processed: {imported}  (new: {inserted}, updated existing: {updated})")
        print(f"Linked to library: {matched}  (by ISBN: {by_isbn}, by title+author: {matched - by_isbn})")
        print(f"Not in library (book_id left empty): {imported - matched}")
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
    csv_path = Path(__file__).parent / 'data' / 'tt storygraph data.csv'
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