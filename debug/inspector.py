import sqlite3

def inspect_database(db_path='ebook_library.db'):
    """Inspect what's actually in the database"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("="*60)
        print("DATABASE INSPECTION")
        print("="*60)
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTables in database: {len(tables)}")
        for (table_name,) in tables:
            print(f"  - {table_name}")
        
        # Count books
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        print(f"\nTotal books: {book_count}")
        
        # Count authors
        cursor.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]
        print(f"Total authors: {author_count}")
        
        # Show some authors
        if author_count > 0:
            cursor.execute("SELECT author_name FROM authors LIMIT 10")
            authors = cursor.fetchall()
            print(f"\nFirst {len(authors)} authors:")
            for (author,) in authors:
                print(f"  - {author}")
        
        # Count subjects
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]
        print(f"\nTotal subjects: {subject_count}")
        
        # Count series
        cursor.execute("SELECT COUNT(*) FROM series")
        series_count = cursor.fetchone()[0]
        print(f"Total series: {series_count}")
        
        # Show some series
        if series_count > 0:
            cursor.execute("SELECT series_name FROM series")
            series = cursor.fetchall()
            print(f"\nAll series found:")
            for (series_name,) in series:
                print(f"  - {series_name}")
        else:
            print("\n⚠️  NO SERIES FOUND IN DATABASE")
            print("\nThis could mean:")
            print("  1. Your OPF files don't have series metadata")
            print("  2. The database was created with old code before series support")
            print("  3. The series metadata isn't being parsed correctly")
        
        # Check a sample book for metadata
        cursor.execute("SELECT id, title, metadata_path FROM books LIMIT 1")
        sample_book = cursor.fetchone()
        
        if sample_book:
            book_id, title, metadata_path = sample_book
            print(f"\n" + "="*60)
            print(f"SAMPLE BOOK: {title}")
            print("="*60)
            print(f"Metadata file: {metadata_path}")
            
            # Check if this book has series
            cursor.execute('''
                SELECT ser.series_name, bser.series_index
                FROM series ser
                JOIN book_series bser ON ser.id = bser.series_id
                WHERE bser.book_id = ?
            ''', (book_id,))
            series_info = cursor.fetchone()
            
            if series_info:
                print(f"Series: {series_info[0]} #{series_info[1]}")
            else:
                print("Series: None")
            
            # Check authors
            cursor.execute('''
                SELECT a.author_name
                FROM authors a
                JOIN book_authors ba ON a.id = ba.author_id
                WHERE ba.book_id = ?
            ''', (book_id,))
            authors = cursor.fetchall()
            if authors:
                print(f"Authors: {', '.join([a[0] for a in authors])}")
            
            # Check subjects
            cursor.execute('''
                SELECT s.subject_name
                FROM subjects s
                JOIN book_subjects bs ON s.id = bs.subject_id
                WHERE bs.book_id = ?
            ''', (book_id,))
            subjects = cursor.fetchall()
            if subjects:
                print(f"Subjects: {', '.join([s[0] for s in subjects[:5]])}")
        
        conn.close()
        
        print("\n" + "="*60)
        
    except sqlite3.OperationalError as e:
        print(f"Error: Database file not found or corrupted")
        print(f"Details: {e}")
    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_database()