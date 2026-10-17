import requests
import sqlite3
import time

def verify_isbn(isbn, title, author):
    """Check if ISBN matches the book title and author using Google Books API"""
    try:
        # Clean ISBN
        isbn_clean = isbn.replace('-', '').replace(' ', '')
        
        # Google Books API
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_clean}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('totalItems', 0) > 0:
                book_info = data['items'][0]['volumeInfo']
                api_title = book_info.get('title', '').lower()
                api_authors = [a.lower() for a in book_info.get('authors', [])]
                
                # Simple match check
                title_match = title.lower() in api_title or api_title in title.lower()
                author_match = any(author.lower() in api_author or api_author in author.lower() 
                                 for api_author in api_authors)
                
                return title_match and author_match, api_title, api_authors
            else:
                return None, None, None  # ISBN not found
        
        return None, None, None
        
    except Exception as e:
        print(f"Error checking ISBN {isbn}: {e}")
        return None, None, None

# Usage with your database
conn = sqlite3.connect('../infra/data/tt_db_ebook_lib.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT b.id, b.title, bi.identifier_value, a.author_name
    FROM books b
    JOIN book_identifiers bi ON b.id = bi.book_id
    JOIN book_authors ba ON b.id = ba.book_id
    JOIN authors a ON ba.author_id = a.id
    WHERE bi.identifier_type = 'ISBN'
    ORDER BY a.last_name, a.first_name
''')

for book_id, title, isbn, author in cursor.fetchall():
    matches, api_title, api_authors = verify_isbn(isbn, title, author)
    
    if matches is None:
        print(f"❌ ISBN {isbn} not found in Google Books")
    elif matches:
        print(f"✓ {title} - ISBN verified")
    else:
        print(f"⚠ {title} - ISBN MISMATCH!")
        print(f"  Expected: {title} by {author}")
        print(f"  API says: {api_title} by {api_authors}")
    
    time.sleep(1)  # Rate limiting

conn.close()