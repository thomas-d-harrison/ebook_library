import os
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

class EbookCatalog:
    def __init__(self, db_path='data/tt_db_ebook_lib.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"Connected to database: {self.db_path}")
    
    def create_tables(self):
        """Create database tables for the ebook library"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                book_folder TEXT,
                isbn TEXT,
                publisher TEXT,
                publish_date TEXT,
                language TEXT,
                description TEXT,
                cover_path TEXT,
                metadata_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT UNIQUE NOT NULL,
                author_sort TEXT,
                first_name TEXT,
                last_name TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_authors (
                book_id INTEGER,
                author_id INTEGER,
                PRIMARY KEY (book_id, author_id),
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES authors (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                file_path TEXT,
                file_format TEXT,
                file_size INTEGER,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_subjects (
                book_id INTEGER,
                subject_id INTEGER,
                PRIMARY KEY (book_id, subject_id),
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_series (
                book_id INTEGER,
                series_id INTEGER,
                series_index REAL,
                PRIMARY KEY (book_id, series_id),
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                FOREIGN KEY (series_id) REFERENCES series (id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
        print("Database tables created successfully")
    
    def parse_opf_metadata(self, opf_path):
        """Parse OPF metadata file and extract book information"""
        metadata = {
            'title': None,
            'authors': [],
            'isbn': None,
            'publisher': None,
            'publish_date': None,
            'language': None,
            'description': None,
            'subjects': [],
            'series': None,
            'series_index': None
        }
        
        try:
            tree = ET.parse(opf_path)
            root = tree.getroot()
            
            # Handle namespaces
            ns = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            # Try without namespace first, then with namespace
            for prefix in ['', 'dc:']:
                if metadata['title'] is None:
                    title_elem = root.find(f'.//{prefix}title', ns if prefix else {})
                    if title_elem is not None:
                        metadata['title'] = title_elem.text
                
                # Extract all authors/creators
                if not metadata['authors']:
                    author_elems = root.findall(f'.//{prefix}creator', ns if prefix else {})
                    for author_elem in author_elems:
                        if author_elem.text:
                            author_name = author_elem.text.strip()
                            # Get the file-as (sort name) attribute
                            author_sort = author_elem.get('{http://www.idpf.org/2007/opf}file-as')
                            if not author_sort:
                                author_sort = author_elem.get('opf:file-as')
                            
                            metadata['authors'].append({
                                'name': author_name,
                                'sort': author_sort
                            })
                
                if metadata['publisher'] is None:
                    pub_elem = root.find(f'.//{prefix}publisher', ns if prefix else {})
                    if pub_elem is not None:
                        metadata['publisher'] = pub_elem.text
                
                if metadata['publish_date'] is None:
                    date_elem = root.find(f'.//{prefix}date', ns if prefix else {})
                    if date_elem is not None:
                        metadata['publish_date'] = date_elem.text
                
                if metadata['language'] is None:
                    lang_elem = root.find(f'.//{prefix}language', ns if prefix else {})
                    if lang_elem is not None:
                        metadata['language'] = lang_elem.text
                
                if metadata['description'] is None:
                    desc_elem = root.find(f'.//{prefix}description', ns if prefix else {})
                    if desc_elem is not None:
                        metadata['description'] = desc_elem.text
                
                if metadata['isbn'] is None:
                    isbn_elem = root.find(f'.//{prefix}identifier[@id="isbn"]', ns if prefix else {})
                    if isbn_elem is None:
                        isbn_elem = root.find(f'.//{prefix}identifier', ns if prefix else {})
                    if isbn_elem is not None:
                        metadata['isbn'] = isbn_elem.text
                
                # Extract all subject elements
                if not metadata['subjects']:
                    subject_elems = root.findall(f'.//{prefix}subject', ns if prefix else {})
                    for subject_elem in subject_elems:
                        if subject_elem.text:
                            metadata['subjects'].append(subject_elem.text.strip())
            
            # Extract series information from meta tags (OUTSIDE the prefix loop)
            series_elem = root.find('.//meta[@name="calibre:series"]')
            if series_elem is None:
                series_elem = root.find('.//opf:meta[@name="calibre:series"]', ns)
            
            if series_elem is not None:
                metadata['series'] = series_elem.get('content')
            
            series_index_elem = root.find('.//meta[@name="calibre:series_index"]')
            if series_index_elem is None:
                series_index_elem = root.find('.//opf:meta[@name="calibre:series_index"]', ns)
            
            if series_index_elem is not None:
                try:
                    metadata['series_index'] = float(series_index_elem.get('content'))
                except (ValueError, TypeError):
                    metadata['series_index'] = None
        
        except Exception as e:
            print(f"Error parsing OPF file {opf_path}: {e}")
        
        return metadata
    
    def parse_author_name(self, author_name, author_sort=None):
        """Parse author name into first and last name"""
        first_name = None
        last_name = None
        
        # If we have a sort name like "Sanderson, Brandon"
        if author_sort and ',' in author_sort:
            parts = author_sort.split(',', 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip() if len(parts) > 1 else None
        else:
            # Try to parse from the regular name
            name_parts = author_name.strip().split()
            if len(name_parts) >= 2:
                # Assume last part is last name, everything else is first name
                last_name = name_parts[-1]
                first_name = ' '.join(name_parts[:-1])
            elif len(name_parts) == 1:
                # Single name, put in last name
                last_name = name_parts[0]
                first_name = None
        
        return first_name, last_name
    
    def add_or_get_author(self, author_name, author_sort=None):
        """Add an author to the authors table or get its ID if it exists"""
        # Parse name into first and last
        first_name, last_name = self.parse_author_name(author_name, author_sort)
        
        try:
            self.cursor.execute('''
                INSERT INTO authors (author_name, author_sort, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            ''', (author_name, author_sort, first_name, last_name))
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Author already exists, get its ID
            self.cursor.execute('SELECT id FROM authors WHERE author_name = ?', (author_name,))
            return self.cursor.fetchone()[0]
    
    def link_book_authors(self, book_id, authors):
        """Link a book to its authors"""
        for author in authors:
            # Handle both old format (string) and new format (dict)
            if isinstance(author, dict):
                author_name = author['name']
                author_sort = author.get('sort')
            else:
                author_name = author
                author_sort = None
            
            author_id = self.add_or_get_author(author_name, author_sort)
            self.cursor.execute('''
                INSERT OR IGNORE INTO book_authors (book_id, author_id)
                VALUES (?, ?)
            ''', (book_id, author_id))
    
    def add_or_get_subject(self, subject_name):
        """Add a subject to the subjects table or get its ID if it exists"""
        try:
            self.cursor.execute('INSERT INTO subjects (subject_name) VALUES (?)', (subject_name,))
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            self.cursor.execute('SELECT id FROM subjects WHERE subject_name = ?', (subject_name,))
            return self.cursor.fetchone()[0]
    
    def link_book_subjects(self, book_id, subjects):
        """Link a book to its subjects"""
        for subject in subjects:
            subject_id = self.add_or_get_subject(subject)
            self.cursor.execute('''
                INSERT OR IGNORE INTO book_subjects (book_id, subject_id)
                VALUES (?, ?)
            ''', (book_id, subject_id))
    
    def add_or_get_series(self, series_name):
        """Add a series to the series table or get its ID if it exists"""
        try:
            self.cursor.execute('INSERT INTO series (series_name) VALUES (?)', (series_name,))
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            self.cursor.execute('SELECT id FROM series WHERE series_name = ?', (series_name,))
            return self.cursor.fetchone()[0]
    
    def link_book_series(self, book_id, series_name, series_index):
        """Link a book to its series with the index number"""
        series_id = self.add_or_get_series(series_name)
        self.cursor.execute('''
            INSERT OR REPLACE INTO book_series (book_id, series_id, series_index)
            VALUES (?, ?, ?)
        ''', (book_id, series_id, series_index))
    
    def scan_library(self, library_path):
        """Scan the library folder structure and add books to database"""
        library_path = Path(library_path)
        
        if not library_path.exists():
            print(f"Error: Library path does not exist: {library_path}")
            return
        
        ignored_folders = {'.calnote', '.archive'}
        books_added = 0
        
        for author_folder in library_path.iterdir():
            if not author_folder.is_dir():
                continue
            
            folder_author_name = author_folder.name
            
            if folder_author_name in ignored_folders:
                print(f"Skipping ignored folder: {folder_author_name}")
                continue
            
            if folder_author_name.startswith('.'):
                print(f"Skipping hidden folder: {folder_author_name}")
                continue
            
            for book_folder in author_folder.iterdir():
                if not book_folder.is_dir():
                    continue
                
                book_name = book_folder.name
                print(f"\nProcessing: {folder_author_name} / {book_name}")
                
                metadata = {'authors': [{'name': folder_author_name, 'sort': None}], 'title': book_name, 'subjects': []}
                opf_file = None
                cover_file = None
                book_files = []
                
                for file in book_folder.iterdir():
                    if file.suffix.lower() == '.opf':
                        opf_file = str(file)
                        parsed_metadata = self.parse_opf_metadata(file)
                        metadata.update(parsed_metadata)
                        if not metadata['authors']:
                            metadata['authors'] = [{'name': folder_author_name, 'sort': None}]
                    elif file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        cover_file = str(file)
                    elif file.suffix.lower() in ['.epub', '.mobi', '.azw', '.azw3', '.pdf', '.txt']:
                        book_files.append(file)
                
                self.cursor.execute('''
                    INSERT INTO books (title, book_folder, isbn, publisher, 
                                     publish_date, language, description, cover_path, metadata_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata.get('title', book_name),
                    str(book_folder),
                    metadata.get('isbn'),
                    metadata.get('publisher'),
                    metadata.get('publish_date'),
                    metadata.get('language'),
                    metadata.get('description'),
                    cover_file,
                    opf_file
                ))
                
                book_id = self.cursor.lastrowid
                
                if metadata.get('authors'):
                    self.link_book_authors(book_id, metadata['authors'])
                
                if metadata.get('subjects'):
                    self.link_book_subjects(book_id, metadata['subjects'])
                
                if metadata.get('series'):
                    self.link_book_series(book_id, metadata['series'], metadata.get('series_index'))
                
                for book_file in book_files:
                    file_size = book_file.stat().st_size
                    self.cursor.execute('''
                        INSERT INTO book_files (book_id, file_path, file_format, file_size)
                        VALUES (?, ?, ?, ?)
                    ''', (book_id, str(book_file), book_file.suffix.lower(), file_size))
                
                books_added += 1
                # Extract author names for display
                authors_display = []
                for author in metadata['authors']:
                    if isinstance(author, dict):
                        authors_display.append(author['name'])
                    else:
                        authors_display.append(author)
                authors_str = ', '.join(authors_display)
                subjects_info = f" | Subjects: {', '.join(metadata['subjects'][:3])}" if metadata.get('subjects') else ""
                series_info = f" | Series: {metadata['series']} #{metadata.get('series_index', '?')}" if metadata.get('series') else ""
                print(f"  ✓ Added: {metadata.get('title', book_name)} by {authors_str}{series_info}{subjects_info}")
        
        self.conn.commit()
        print(f"\n{'='*50}")
        print(f"Successfully added {books_added} books to the database!")
    
    def search_books(self, query):
        """Search for books by title, author, subject, or series"""
        self.cursor.execute('''
            SELECT DISTINCT b.id, b.title, b.book_folder 
            FROM books b
            LEFT JOIN book_authors ba ON b.id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.id
            LEFT JOIN book_subjects bs ON b.id = bs.book_id
            LEFT JOIN subjects s ON bs.subject_id = s.id
            LEFT JOIN book_series bser ON b.id = bser.book_id
            LEFT JOIN series ser ON bser.series_id = ser.id
            WHERE b.title LIKE ? OR a.author_name LIKE ? OR s.subject_name LIKE ? OR ser.series_name LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        results = self.cursor.fetchall()
        return results
    
    def get_book_details(self, book_id):
        """Get detailed information about a specific book"""
        self.cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = self.cursor.fetchone()
        
        self.cursor.execute('SELECT * FROM book_files WHERE book_id = ?', (book_id,))
        files = self.cursor.fetchall()
        
        self.cursor.execute('''
            SELECT a.author_name 
            FROM authors a
            JOIN book_authors ba ON a.id = ba.author_id
            WHERE ba.book_id = ?
        ''', (book_id,))
        authors = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute('''
            SELECT s.subject_name 
            FROM subjects s
            JOIN book_subjects bs ON s.id = bs.subject_id
            WHERE bs.book_id = ?
        ''', (book_id,))
        subjects = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute('''
            SELECT ser.series_name, bser.series_index
            FROM series ser
            JOIN book_series bser ON ser.id = bser.series_id
            WHERE bser.book_id = ?
        ''', (book_id,))
        series_info = self.cursor.fetchone()
        
        return book, files, authors, subjects, series_info
    
    def get_all_authors(self):
        """Get all unique authors in the library"""
        self.cursor.execute('SELECT id, author_name FROM authors ORDER BY author_name')
        return self.cursor.fetchall()
    
    def get_books_by_author(self, author_name):
        """Get all books by a specific author"""
        self.cursor.execute('''
            SELECT b.id, b.title
            FROM books b
            JOIN book_authors ba ON b.id = ba.book_id
            JOIN authors a ON ba.author_id = a.id
            WHERE a.author_name = ?
        ''', (author_name,))
        return self.cursor.fetchall()
    
    def get_all_subjects(self):
        """Get all unique subjects in the library"""
        self.cursor.execute('SELECT id, subject_name FROM subjects ORDER BY subject_name')
        return self.cursor.fetchall()
    
    def get_books_by_subject(self, subject_name):
        """Get all books with a specific subject"""
        self.cursor.execute('''
            SELECT b.id, b.title
            FROM books b
            JOIN book_subjects bs ON b.id = bs.book_id
            JOIN subjects s ON bs.subject_id = s.id
            WHERE s.subject_name = ?
        ''', (subject_name,))
        return self.cursor.fetchall()
    
    def get_all_series(self):
        """Get all unique series in the library"""
        self.cursor.execute('SELECT id, series_name FROM series ORDER BY series_name')
        return self.cursor.fetchall()
    
    def get_books_by_series(self, series_name):
        """Get all books in a specific series, ordered by series index"""
        self.cursor.execute('''
            SELECT b.id, b.title, bser.series_index
            FROM books b
            JOIN book_series bser ON b.id = bser.book_id
            JOIN series ser ON bser.series_id = ser.id
            WHERE ser.series_name = ?
            ORDER BY bser.series_index
        ''', (series_name,))
        return self.cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    print("="*50)
    print("Ebook Library Cataloger")
    print("="*50)
    
    library_path = input("\nEnter the path to your ebook library folder: ").strip()
    library_path = library_path.strip('"').strip("'")
    
    catalog = EbookCatalog()
    catalog.connect()
    catalog.create_tables()
    
    catalog.scan_library(library_path)
    
    print("\n" + "="*50)
    print("All series found in your library:")
    print("="*50)
    all_series = catalog.get_all_series()
    if all_series:
        for series_id, series_name in all_series:
            books = catalog.get_books_by_series(series_name)
            print(f"\n{series_name} ({len(books)} books):")
            for book_id, title, series_index in books:
                index_str = f"#{series_index}" if series_index else "#?"
                print(f"  {index_str} - {title}")
    else:
        print("No series found in metadata files.")
    
    print("\n" + "="*50)
    print("Database created! You can now explore your library.")
    
    while True:
        print("\n" + "="*50)
        print("MENU OPTIONS:")
        print("="*50)
        print("1. Search books (by title, author, subject, or series)")
        print("2. Browse series")
        print("3. View books in a specific series")
        print("4. List all authors")
        print("5. List all subjects")
        print("6. Quit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            search_query = input("\nEnter search term: ").strip()
            results = catalog.search_books(search_query)
            if results:
                print(f"\nFound {len(results)} book(s):")
                for book in results:
                    catalog.cursor.execute('''
                        SELECT a.author_name 
                        FROM authors a
                        JOIN book_authors ba ON a.id = ba.author_id
                        WHERE ba.book_id = ?
                    ''', (book[0],))
                    authors = [row[0] for row in catalog.cursor.fetchall()]
                    authors_str = ', '.join(authors) if authors else 'Unknown'
                    
                    catalog.cursor.execute('''
                        SELECT ser.series_name, bser.series_index
                        FROM series ser
                        JOIN book_series bser ON ser.id = bser.series_id
                        WHERE bser.book_id = ?
                    ''', (book[0],))
                    series_result = catalog.cursor.fetchone()
                    series_str = f" ({series_result[0]} #{series_result[1]})" if series_result else ""
                    
                    print(f"  ID: {book[0]} | {book[1]} by {authors_str}{series_str}")
            else:
                print("No books found.")
        
        elif choice == '2':
            all_series = catalog.get_all_series()
            if all_series:
                print(f"\nFound {len(all_series)} series:")
                for series_id, series_name in all_series:
                    books = catalog.get_books_by_series(series_name)
                    print(f"  {series_name} ({len(books)} books)")
            else:
                print("No series found.")
        
        elif choice == '3':
            series_name = input("\nEnter series name: ").strip()
            books = catalog.get_books_by_series(series_name)
            if books:
                print(f"\n{series_name} ({len(books)} books):")
                for book_id, title, series_index in books:
                    index_str = f"#{series_index}" if series_index else "#?"
                    print(f"  {index_str} - {title}")
            else:
                print(f"No books found in series: {series_name}")
        
        elif choice == '4':
            authors = catalog.get_all_authors()
            print(f"\nFound {len(authors)} authors:")
            for author_id, author_name in authors:
                books = catalog.get_books_by_author(author_name)
                print(f"  {author_name} ({len(books)} books)")
        
        elif choice == '5':
            subjects = catalog.get_all_subjects()
            print(f"\nFound {len(subjects)} subjects:")
            for subject_id, subject_name in subjects[:50]:
                print(f"  {subject_name}")
            if len(subjects) > 50:
                print(f"  ... and {len(subjects) - 50} more")
        
        elif choice == '6':
            break
        
        else:
            print("Invalid choice. Please enter 1-6.")
    
    catalog.close()
    print("\nDone!")