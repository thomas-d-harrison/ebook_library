from flask import Flask, render_template_string, jsonify, send_file
import sqlite3
import os

app = Flask(__name__)

DB_PATH = 'tt_db_ebook_lib.db'

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Family Library Catalog</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        .search-bar {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        .search-input {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #ddd;
            border-radius: 10px;
            transition: border 0.3s;
        }
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .filters {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        .filter-btn:hover, .filter-btn.active {
            background: #667eea;
            color: white;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .books-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .book-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        .book-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .book-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .book-author {
            color: #667eea;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        .book-series {
            background: #f0f0f0;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        .book-subjects {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 10px;
        }
        .subject-tag {
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
        }
        .no-results {
            text-align: center;
            padding: 50px;
            background: white;
            border-radius: 15px;
            color: #666;
            font-size: 1.2em;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: white;
            font-size: 1.5em;
        }
        
        /* Modal styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            overflow-y: auto;
        }
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .modal-content {
            background: white;
            border-radius: 20px;
            max-width: 800px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        .modal-header {
            padding: 30px;
            border-bottom: 2px solid #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: start;
        }
        .close-btn {
            background: none;
            border: none;
            font-size: 2em;
            cursor: pointer;
            color: #999;
            line-height: 1;
        }
        .close-btn:hover {
            color: #333;
        }
        .modal-body {
            padding: 30px;
        }
        .book-detail-grid {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .book-cover {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .book-cover-placeholder {
            width: 100%;
            height: 300px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 3em;
        }
        .book-info h2 {
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }
        .book-info .author {
            color: #667eea;
            font-size: 1.3em;
            margin-bottom: 15px;
        }
        .info-row {
            margin-bottom: 15px;
        }
        .info-label {
            font-weight: bold;
            color: #666;
            margin-bottom: 5px;
        }
        .info-value {
            color: #333;
        }
        .description {
            margin: 20px 0;
            line-height: 1.6;
            color: #666;
        }
        .download-section {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #f0f0f0;
        }
        .download-btn {
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 10px;
            margin-right: 10px;
            margin-bottom: 10px;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            font-size: 1em;
        }
        .download-btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .format-badge {
            background: #f0f0f0;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.8em;
            margin-left: 5px;
        }
        
        @media (max-width: 768px) {
            .book-detail-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Family Library Catalog</h1>
            <p class="subtitle">Browse and download our ebook collection</p>
        </header>
        <div class="search-bar">
            <input type="text" class="search-input" id="searchInput" placeholder="Search by title, author, or subject...">
            <div class="filters">
                <button class="filter-btn active" data-filter="all">All Books</button>
                <button class="filter-btn" data-filter="series">In Series</button>
                <button class="filter-btn" data-filter="standalone">Standalone</button>
            </div>
        </div>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalBooks">0</div>
                <div class="stat-label">Total Books</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalAuthors">0</div>
                <div class="stat-label">Authors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalSeries">0</div>
                <div class="stat-label">Series</div>
            </div>
        </div>
        <div id="booksContainer">
            <div class="loading">Loading library...</div>
        </div>
    </div>
    
    <!-- Modal for book details -->
    <div id="bookModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div></div>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody">
                <div class="loading">Loading book details...</div>
            </div>
        </div>
    </div>
    
    <script>
        let allBooks = [];
        let currentFilter = 'all';

        async function loadBooks() {
            try {
                const response = await fetch('/api/books');
                const data = await response.json();
                allBooks = data.books;
                displayBooks(allBooks);
                updateStats(data.stats);
            } catch (error) {
                document.getElementById('booksContainer').innerHTML = 
                    '<div class="no-results">Error loading books</div>';
            }
        }

        function displayBooks(books) {
            const container = document.getElementById('booksContainer');
            if (books.length === 0) {
                container.innerHTML = '<div class="no-results">No books found</div>';
                return;
            }
            container.innerHTML = '<div class="books-grid">' + 
                books.map(book => `
                    <div class="book-card" onclick="showBookDetails(${book.id})">
                        <div class="book-title">${book.title}</div>
                        <div class="book-author">by ${book.authors}</div>
                        ${book.series ? `<div class="book-series">${book.series}</div>` : ''}
                        ${book.subjects.length > 0 ? `
                            <div class="book-subjects">
                                ${book.subjects.map(s => `<span class="subject-tag">${s}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `).join('') + 
                '</div>';
        }

        async function showBookDetails(bookId) {
            const modal = document.getElementById('bookModal');
            const modalBody = document.getElementById('modalBody');
            
            modal.classList.add('active');
            modalBody.innerHTML = '<div class="loading">Loading book details...</div>';
            
            try {
                const response = await fetch(`/api/book/${bookId}`);
                const book = await response.json();
                
                modalBody.innerHTML = `
                    <div class="book-detail-grid">
                        <div>
                            ${book.cover_path ? 
                                `<img src="/api/cover/${bookId}" class="book-cover" alt="${book.title} cover">` :
                                `<div class="book-cover-placeholder">📚</div>`
                            }
                        </div>
                        <div class="book-info">
                            <h2>${book.title}</h2>
                            <div class="author">${book.authors}</div>
                            ${book.series ? `
                                <div class="info-row">
                                    <div class="info-label">Series</div>
                                    <div class="info-value">${book.series}</div>
                                </div>
                            ` : ''}
                            ${book.publisher ? `
                                <div class="info-row">
                                    <div class="info-label">Publisher</div>
                                    <div class="info-value">${book.publisher}</div>
                                </div>
                            ` : ''}
                            ${book.publish_date ? `
                                <div class="info-row">
                                    <div class="info-label">Published</div>
                                    <div class="info-value">${book.publish_date}</div>
                                </div>
                            ` : ''}
                            ${book.isbn ? `
                                <div class="info-row">
                                    <div class="info-label">ISBN</div>
                                    <div class="info-value">${book.isbn}</div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    ${book.subjects.length > 0 ? `
                        <div class="info-row">
                            <div class="info-label">Subjects</div>
                            <div class="book-subjects">
                                ${book.subjects.map(s => `<span class="subject-tag">${s}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${book.description ? `
                        <div class="info-row">
                            <div class="info-label">Description</div>
                            <div class="description">${book.description}</div>
                        </div>
                    ` : ''}
                    
                    ${book.files.length > 0 ? `
                        <div class="download-section">
                            <div class="info-label">Download Book</div>
                            ${book.files.map(file => `
                                <a href="/api/download/${file.id}" class="download-btn" download>
                                    Download <span class="format-badge">${file.format.toUpperCase()}</span>
                                </a>
                            `).join('')}
                        </div>
                    ` : ''}
                `;
            } catch (error) {
                modalBody.innerHTML = '<div class="no-results">Error loading book details</div>';
            }
        }

        function closeModal() {
            document.getElementById('bookModal').classList.remove('active');
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('bookModal');
            if (event.target === modal) {
                closeModal();
            }
        }

        function filterBooks(searchTerm, filterType) {
            let filtered = allBooks;
            if (filterType === 'series') {
                filtered = filtered.filter(book => book.series !== null);
            } else if (filterType === 'standalone') {
                filtered = filtered.filter(book => book.series === null);
            }
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                filtered = filtered.filter(book => 
                    book.title.toLowerCase().includes(term) ||
                    book.authors.toLowerCase().includes(term) ||
                    book.subjects.some(s => s.toLowerCase().includes(term))
                );
            }
            displayBooks(filtered);
        }

        function updateStats(stats) {
            document.getElementById('totalBooks').textContent = stats.total_books;
            document.getElementById('totalAuthors').textContent = stats.total_authors;
            document.getElementById('totalSeries').textContent = stats.total_series;
        }

        document.getElementById('searchInput').addEventListener('input', (e) => {
            filterBooks(e.target.value, currentFilter);
        });

        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                filterBooks(document.getElementById('searchInput').value, currentFilter);
            });
        });

        loadBooks();
    </script>
</body>
</html>
'''

def get_all_books():
    """Get all books with their details from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title FROM books ORDER BY title')
    books = cursor.fetchall()
    
    result = []
    for book_id, title in books:
        cursor.execute('''
            SELECT a.author_name 
            FROM authors a
            JOIN book_authors ba ON a.id = ba.author_id
            WHERE ba.book_id = ?
        ''', (book_id,))
        authors = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT ser.series_name, bser.series_index
            FROM series ser
            JOIN book_series bser ON ser.id = bser.series_id
            WHERE bser.book_id = ?
        ''', (book_id,))
        series_result = cursor.fetchone()
        series = f"{series_result[0]} #{series_result[1]}" if series_result else None
        
        cursor.execute('''
            SELECT s.subject_name 
            FROM subjects s
            JOIN book_subjects bs ON s.id = bs.subject_id
            WHERE bs.book_id = ?
            LIMIT 5
        ''', (book_id,))
        subjects = [row[0] for row in cursor.fetchall()]
        
        result.append({
            'id': book_id,
            'title': title,
            'authors': ', '.join(authors) if authors else 'Unknown',
            'series': series,
            'subjects': subjects
        })
    
    conn.close()
    return result

def get_book_details(book_id):
    """Get detailed information about a specific book"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book_row = cursor.fetchone()
    
    if not book_row:
        conn.close()
        return None
    
    # Get authors
    cursor.execute('''
        SELECT a.author_name 
        FROM authors a
        JOIN book_authors ba ON a.id = ba.author_id
        WHERE ba.book_id = ?
    ''', (book_id,))
    authors = [row[0] for row in cursor.fetchall()]
    
    # Get series
    cursor.execute('''
        SELECT ser.series_name, bser.series_index
        FROM series ser
        JOIN book_series bser ON ser.id = bser.series_id
        WHERE bser.book_id = ?
    ''', (book_id,))
    series_result = cursor.fetchone()
    series = f"{series_result[0]} #{series_result[1]}" if series_result else None
    
    # Get subjects
    cursor.execute('''
        SELECT s.subject_name 
        FROM subjects s
        JOIN book_subjects bs ON s.id = bs.subject_id
        WHERE bs.book_id = ?
    ''', (book_id,))
    subjects = [row[0] for row in cursor.fetchall()]
    
    # Get files
    cursor.execute('SELECT id, file_path, file_format FROM book_files WHERE book_id = ?', (book_id,))
    files = [{'id': row[0], 'path': row[1], 'format': row[2].replace('.', '')} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'id': book_row[0],
        'title': book_row[1],
        'authors': ', '.join(authors) if authors else 'Unknown',
        'isbn': book_row[3],
        'publisher': book_row[4],
        'publish_date': book_row[5],
        'description': book_row[7],
        'cover_path': book_row[8],
        'series': series,
        'subjects': subjects,
        'files': files
    }

def get_stats():
    """Get library statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM books')
    total_books = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM authors')
    total_authors = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM series')
    total_series = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_books': total_books,
        'total_authors': total_authors,
        'total_series': total_series
    }

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/books')
def api_books():
    books = get_all_books()
    stats = get_stats()
    return jsonify({
        'books': books,
        'stats': stats
    })

@app.route('/api/book/<int:book_id>')
def api_book_details(book_id):
    book = get_book_details(book_id)
    if book:
        return jsonify(book)
    return jsonify({'error': 'Book not found'}), 404

@app.route('/api/cover/<int:book_id>')
def api_cover(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT cover_path FROM books WHERE id = ?', (book_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0])
    return '', 404

@app.route('/api/download/<int:file_id>')
def api_download(file_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM book_files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0], as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found!")
        print("Make sure ebook_library.db is in the same folder as this script.")
    else:
        print("="*60)
        print("Family Library Web Catalog")
        print("="*60)
        print("\nStarting server...")
        print("\nOpen your browser and go to:")
        print("  http://localhost:5000")
        print("\nOr share with family on your network:")
        print("  http://YOUR_COMPUTER_IP:5000")
        print("\nPress Ctrl+C to stop the server")
        print("="*60)
        app.run(host='0.0.0.0', port=5000, debug=True)