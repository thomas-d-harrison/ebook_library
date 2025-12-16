import sqlite3

def analyze_database(db_path='ebook_library.db'):
    """Analyze the database to find books with and without relationships"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("="*60)
    print("DATABASE ANALYSIS")
    print("="*60)
    
    # Overall counts
    print("\n1. OVERALL COUNTS:")
    print("-" * 60)
    cursor.execute('SELECT COUNT(*) FROM books')
    total_books = cursor.fetchone()[0]
    print(f"   Total books: {total_books}")
    
    cursor.execute('SELECT COUNT(*) FROM authors')
    total_authors = cursor.fetchone()[0]
    print(f"   Total authors: {total_authors}")
    
    cursor.execute('SELECT COUNT(*) FROM subjects')
    total_subjects = cursor.fetchone()[0]
    print(f"   Total subjects: {total_subjects}")
    
    cursor.execute('SELECT COUNT(*) FROM book_authors')
    total_ba = cursor.fetchone()[0]
    print(f"   Total book-author links: {total_ba}")
    
    cursor.execute('SELECT COUNT(*) FROM book_subjects')
    total_bs = cursor.fetchone()[0]
    print(f"   Total book-subject links: {total_bs}")
    
    # Books with authors
    print("\n2. BOOKS WITH AUTHORS:")
    print("-" * 60)
    cursor.execute('''
        SELECT COUNT(DISTINCT book_id) FROM book_authors
    ''')
    books_with_authors = cursor.fetchone()[0]
    print(f"   Books with at least one author: {books_with_authors}")
    print(f"   Books WITHOUT authors: {total_books - books_with_authors}")
    
    # Books with subjects
    print("\n3. BOOKS WITH SUBJECTS:")
    print("-" * 60)
    cursor.execute('''
        SELECT COUNT(DISTINCT book_id) FROM book_subjects
    ''')
    books_with_subjects = cursor.fetchone()[0]
    print(f"   Books with at least one subject: {books_with_subjects}")
    print(f"   Books WITHOUT subjects: {total_books - books_with_subjects}")
    
    # Sample books WITH authors
    print("\n4. SAMPLE BOOKS WITH AUTHORS (first 5):")
    print("-" * 60)
    cursor.execute('''
        SELECT DISTINCT
            b.id,
            b.title,
            GROUP_CONCAT(a.author_name, ', ') as authors
        FROM books b
        JOIN book_authors ba ON b.id = ba.book_id
        JOIN authors a ON ba.author_id = a.id
        GROUP BY b.id
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"   ID {row[0]}: {row[1]}")
        print(f"      Authors: {row[2]}")
    
    # Sample books WITH subjects
    print("\n5. SAMPLE BOOKS WITH SUBJECTS (first 5):")
    print("-" * 60)
    cursor.execute('''
        SELECT DISTINCT
            b.id,
            b.title,
            GROUP_CONCAT(s.subject_name, ', ') as subjects
        FROM books b
        JOIN book_subjects bs ON b.id = bs.book_id
        JOIN subjects s ON bs.subject_id = s.id
        GROUP BY b.id
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"   ID {row[0]}: {row[1]}")
        print(f"      Subjects: {row[2]}")
    
    # Books WITHOUT authors
    print("\n6. BOOKS WITHOUT AUTHORS (first 10):")
    print("-" * 60)
    cursor.execute('''
        SELECT b.id, b.title, b.book_folder
        FROM books b
        WHERE b.id NOT IN (SELECT DISTINCT book_id FROM book_authors)
        LIMIT 10
    ''')
    orphan_books = cursor.fetchall()
    if orphan_books:
        for row in orphan_books:
            print(f"   ID {row[0]}: {row[1]}")
            print(f"      Folder: {row[2]}")
    else:
        print("   (none)")
    
    # Check if old schema exists
    print("\n7. SCHEMA CHECK:")
    print("-" * 60)
    cursor.execute("PRAGMA table_info(books)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"   Columns in books table: {', '.join(columns)}")
    
    if 'author' in columns:
        print("\n   ⚠️  WARNING: Old 'author' column still exists!")
        cursor.execute('SELECT id, title, author FROM books WHERE author IS NOT NULL LIMIT 3')
        old_data = cursor.fetchall()
        if old_data:
            print("   Books with data in old 'author' column:")
            for row in old_data:
                print(f"      ID {row[0]}: {row[1]} - Author: {row[2]}")
    
    # Test a working query
    if books_with_authors > 0:
        print("\n8. TEST QUERY (book with authors):")
        print("-" * 60)
        cursor.execute('''
            SELECT b.id
            FROM books b
            JOIN book_authors ba ON b.id = ba.book_id
            LIMIT 1
        ''')
        working_book_id = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT 
                b.id,
                b.title,
                GROUP_CONCAT(a.author_name, ', ') as authors
            FROM books b
            LEFT JOIN book_authors ba ON b.id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.id
            WHERE b.id = ?
            GROUP BY b.id
        ''', (working_book_id,))
        result = cursor.fetchone()
        print(f"   Testing with Book ID: {result[0]}")
        print(f"   Title: {result[1]}")
        print(f"   Authors: {result[2]}")
        print("\n   ✓ Query works for books with authors!")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print("\nCONCLUSION:")
    if books_with_authors == 0 and total_ba > 0:
        print("⚠️  You have author links but no books connected to them.")
        print("   There may be a data integrity issue.")
    elif books_with_authors == 0:
        print("⚠️  No books have been linked to authors yet.")
        print("   You may need to re-scan your library with the updated code.")
    elif books_with_authors < total_books:
        print(f"✓  {books_with_authors} books have authors.")
        print(f"⚠️  {total_books - books_with_authors} books are missing author links.")
    else:
        print("✓  All books have author links!")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    db_path = 'ebook_library.db'
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"Analyzing database: {db_path}\n")
    analyze_database(db_path)