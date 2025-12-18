import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / '..' / 'infra' / 'data' / 'tt_db_ebook_lib.db'

def view_series(series_name=None):
    """View books in a series from command line"""
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # If no series name provided, list all series
    if not series_name:
        print("="*60)
        print("ALL SERIES IN YOUR LIBRARY:")
        print("="*60)
        
        cursor.execute('SELECT id, series_name FROM series ORDER BY series_name')
        all_series = cursor.fetchall()
        
        if all_series:
            for series_id, name in all_series:
                cursor.execute('''
                    SELECT COUNT(*) FROM book_series WHERE series_id = ?
                ''', (series_id,))
                book_count = cursor.fetchone()[0]
                print(f"  {name} ({book_count} books)")
        else:
            print("  No series found in database.")
        
        conn.close()
        return
    
    # Show books in the specified series
    print("="*60)
    print(f"BOOKS IN SERIES: {series_name}")
    print("="*60)
    
    cursor.execute('''
        SELECT b.id, b.title, bser.series_index, a.author_name
        FROM books b
        JOIN book_series bser ON b.id = bser.book_id
        JOIN series ser ON bser.series_id = ser.id
        LEFT JOIN book_authors ba ON b.id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.id
        WHERE ser.series_name = ?
        ORDER BY bser.series_index
    ''', (series_name,))
    
    books = cursor.fetchall()
    
    if books:
        print(f"\nFound {len(books)} book(s):\n")
        for book_id, title, series_index, author in books:
            index_str = f"#{series_index}" if series_index else "#?"
            author_str = f"by {author}" if author else ""
            print(f"  {index_str:6} - {title} {author_str}")
    else:
        print(f"\nNo books found in series: {series_name}")
        print("\nDid you mean one of these?")
        
        # Try to find similar series names
        cursor.execute('SELECT series_name FROM series')
        all_series = cursor.fetchall()
        for (name,) in all_series:
            if series_name.lower() in name.lower():
                print(f"  - {name}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Series name provided as command line argument
        series_name = ' '.join(sys.argv[1:])
        view_series(series_name)
    else:
        # No argument - list all series
        view_series()