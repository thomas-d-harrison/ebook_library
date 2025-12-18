from flask import Flask, render_template_string
import sqlite3
import os

app = Flask(__name__)

# Database is in ../infra/data/tt_db_ebook_lib.db
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'infra', 'data', 'tt_db_ebook_lib.db')

COVER_WALL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Cover Wall</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 30px 20px;
            color: white;
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #999;
            font-size: 1.2em;
        }
        
        .view-controls {
            text-align: center;
            margin: 20px 0;
        }
        
        .view-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .view-btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        .view-btn.active {
            background: #764ba2;
        }
        
        .size-slider {
            width: 300px;
            margin: 20px auto;
            display: block;
        }
        
        .cover-grid {
            display: grid;
            gap: 20px;
            padding: 20px;
            max-width: 1800px;
            margin: 0 auto;
            justify-content: center;
        }
        
        .grid-small {
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 15px;
        }
        
        .grid-medium {
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
        }
        
        .grid-large {
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 25px;
        }
        
        .cover-item {
            position: relative;
            cursor: pointer;
            transition: all 0.3s ease;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .cover-item:hover {
            transform: scale(1.05) translateY(-5px);
            z-index: 10;
            box-shadow: 0 20px 40px rgba(0,0,0,0.8);
        }
        
        .cover-image {
            width: 100%;
            height: auto;
            display: block;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }
        
        .cover-placeholder {
            width: 100%;
            aspect-ratio: 2/3;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            color: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }
        
        .cover-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
            padding: 15px;
            opacity: 0;
            transition: opacity 0.3s;
            color: white;
        }
        
        .cover-item:hover .cover-overlay {
            opacity: 1;
        }
        
        .cover-title {
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .cover-author {
            font-size: 0.8em;
            color: #ccc;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .stats {
            text-align: center;
            color: #999;
            margin: 20px 0;
            font-size: 1.1em;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 2em;
            padding: 100px;
        }
        
        /* Fullscreen view */
        .fullscreen-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            align-items: center;
            justify-content: center;
        }
        
        .fullscreen-modal.active {
            display: flex;
        }
        
        .fullscreen-content {
            max-width: 90%;
            max-height: 90vh;
            text-align: center;
        }
        
        .fullscreen-image {
            max-width: 100%;
            max-height: 80vh;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        }
        
        .fullscreen-info {
            color: white;
            margin-top: 20px;
        }
        
        .fullscreen-title {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .fullscreen-author {
            font-size: 1.5em;
            color: #667eea;
        }
        
        .close-fullscreen {
            position: absolute;
            top: 20px;
            right: 40px;
            font-size: 3em;
            color: white;
            cursor: pointer;
            background: none;
            border: none;
        }
        
        .close-fullscreen:hover {
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Book Cover Wall</h1>
        <p class="subtitle">Your library at a glance</p>
    </div>
    
    <div class="view-controls">
        <button class="view-btn" onclick="setGridSize('small')">Small</button>
        <button class="view-btn active" onclick="setGridSize('medium')">Medium</button>
        <button class="view-btn" onclick="setGridSize('large')">Large</button>
    </div>
    
    <div class="stats" id="stats">Loading covers...</div>
    
    <div class="cover-grid grid-medium" id="coverGrid">
        <div class="loading">Loading book covers...</div>
    </div>
    
    <div class="fullscreen-modal" id="fullscreenModal">
        <button class="close-fullscreen" onclick="closeFullscreen()">&times;</button>
        <div class="fullscreen-content" id="fullscreenContent"></div>
    </div>
    
    <script>
        let allBooks = [];
        
        async function loadCovers() {
            try {
                const response = await fetch('/api/books-with-covers');
                const data = await response.json();
                allBooks = data.books;
                displayCovers(allBooks);
                updateStats(data.stats);
            } catch (error) {
                document.getElementById('coverGrid').innerHTML = 
                    '<div class="loading">Error loading covers</div>';
            }
        }
        
        function displayCovers(books) {
            const grid = document.getElementById('coverGrid');
            
            if (books.length === 0) {
                grid.innerHTML = '<div class="loading">No books found</div>';
                return;
            }
            
            grid.innerHTML = books.map(book => `
                <div class="cover-item" onclick="showFullscreen(${book.id})">
                    ${book.has_cover ? 
                        `<img src="/api/cover/${book.id}" class="cover-image" alt="${book.title}">` :
                        `<div class="cover-placeholder">📖</div>`
                    }
                    <div class="cover-overlay">
                        <div class="cover-title">${book.title}</div>
                        <div class="cover-author">${book.authors}</div>
                    </div>
                </div>
            `).join('');
        }
        
        function setGridSize(size) {
            const grid = document.getElementById('coverGrid');
            grid.className = 'cover-grid grid-' + size;
            
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        function showFullscreen(bookId) {
            const book = allBooks.find(b => b.id === bookId);
            if (!book) return;
            
            const modal = document.getElementById('fullscreenModal');
            const content = document.getElementById('fullscreenContent');
            
            content.innerHTML = `
                ${book.has_cover ? 
                    `<img src="/api/cover/${book.id}" class="fullscreen-image" alt="${book.title}">` :
                    `<div class="cover-placeholder" style="width: 400px; height: 600px; margin: 0 auto;">📖</div>`
                }
                <div class="fullscreen-info">
                    <div class="fullscreen-title">${book.title}</div>
                    <div class="fullscreen-author">${book.authors}</div>
                    ${book.series ? `<div style="color: #999; margin-top: 10px;">${book.series}</div>` : ''}
                </div>
            `;
            
            modal.classList.add('active');
        }
        
        function closeFullscreen() {
            document.getElementById('fullscreenModal').classList.remove('active');
        }
        
        function updateStats(stats) {
            document.getElementById('stats').innerHTML = 
                `Displaying ${stats.books_with_covers} books with covers (${stats.total_books} total books)`;
        }
        
        // Close fullscreen on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeFullscreen();
        });
        
        // Close fullscreen when clicking outside
        document.getElementById('fullscreenModal').addEventListener('click', (e) => {
            if (e.target.id === 'fullscreenModal') closeFullscreen();
        });
        
        loadCovers();
    </script>
</body>
</html>
'''

def get_books_with_covers():
    """Get all books and indicate which have covers"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, cover_path FROM books ORDER BY title')
    books = cursor.fetchall()
    
    result = []
    books_with_covers = 0
    
    for book_id, title, cover_path in books:
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
        
        has_cover = cover_path is not None and os.path.exists(cover_path)
        if has_cover:
            books_with_covers += 1
        
        result.append({
            'id': book_id,
            'title': title,
            'authors': ', '.join(authors) if authors else 'Unknown',
            'series': series,
            'has_cover': has_cover
        })
    
    conn.close()
    
    return result, books_with_covers

@app.route('/')
def index():
    return render_template_string(COVER_WALL_TEMPLATE)

@app.route('/api/books-with-covers')
def api_books_with_covers():
    from flask import jsonify
    books, books_with_covers = get_books_with_covers()
    return jsonify({
        'books': books,
        'stats': {
            'total_books': len(books),
            'books_with_covers': books_with_covers
        }
    })

@app.route('/api/cover/<int:book_id>')
def api_cover(book_id):
    from flask import send_file
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT cover_path FROM books WHERE id = ?', (book_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0])
    return '', 404

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found!")
        print("Make sure ebook_library.db is in the same folder as this script.")
    else:
        print("="*60)
        print("Book Cover Wall Display")
        print("="*60)
        print("\nStarting server...")
        print("\nOpen your browser and go to:")
        print("  http://localhost:5000")
        print("\nThis creates a beautiful grid of all your book covers!")
        print("Press Ctrl+C to stop the server")
        print("="*60)
        app.run(host='0.0.0.0', port=5000, debug=True)