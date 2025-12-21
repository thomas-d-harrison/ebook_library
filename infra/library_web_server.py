from flask import Flask, render_template_string, jsonify, send_file
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)

# Database is in ../infra/data/tt_db_ebook_lib.db
DB_PATH = Path(__file__).parent / '..' / 'infra' / 'data' / 'tt_db_ebook_lib.db'

# HTML template - will be added in next message due to length
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TT's eLibrary</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a4d2e 0%, #2d5f3f 50%, #4a7c59 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 30px;
            text-align: center;
            position: relative;
        }
        h1 { color: #1a4d2e; font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { color: #4a7c59; font-size: 1.1em; margin-bottom: 15px; }
        .total-books-badge {
            display: inline-block;
            background: linear-gradient(135deg, #2d5f3f 0%, #4a7c59 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: bold;
            margin-top: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        .search-bar {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }
        .search-input {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #4a7c59;
            border-radius: 10px;
            transition: border 0.3s;
        }
        .search-input:focus {
            outline: none;
            border-color: #2d5f3f;
            box-shadow: 0 0 10px rgba(45, 95, 63, 0.3);
        }
        .filters {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #4a7c59;
            background: white;
            color: #2d5f3f;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        .filter-btn:hover, .filter-btn.active {
            background: #4a7c59;
            color: white;
        }
        .advanced-filters {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e8f5e9;
        }
        .filter-toggle {
            padding: 6px 14px;
            border: 1px solid #4a7c59;
            background: white;
            color: #4a7c59;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
        }
        .filter-toggle.active {
            background: #4a7c59;
            color: white;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }
        .stat-number { font-size: 2.5em; font-weight: bold; color: #2d5f3f; }
        .stat-label { color: #4a7c59; margin-top: 5px; }
        .books-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .book-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
            display: flex;
            gap: 15px;
            position: relative;
        }
        .book-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }
        .reading-status-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .status-read { background: #4caf50; color: white; }
        .status-reading { background: #ff9800; color: white; }
        .status-to-read { background: #9e9e9e; color: white; }
        .book-rating { color: #ffa726; font-size: 0.9em; margin-top: 4px; }
        .book-card-cover {
            flex-shrink: 0;
            width: 80px;
            height: 120px;
            border-radius: 5px;
            object-fit: cover;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
        }
        .book-card-cover-placeholder {
            flex-shrink: 0;
            width: 80px;
            height: 120px;
            background: linear-gradient(135deg, #2d5f3f 0%, #4a7c59 100%);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2em;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
        }
        .book-card-info {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .book-title {
            font-size: 1.25em;
            font-weight: bold;
            color: #1a4d2e;
            margin-bottom: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            line-height: 1.3;
        }
        .book-author {
            color: #4a7c59;
            font-size: 1.05em;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .book-series {
            background: #e8f5e9;
            padding: 4px 10px;
            border-radius: 5px;
            display: inline-block;
            font-size: 0.9em;
            color: #2d5f3f;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100%;
        }
        .book-subjects {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 8px;
            align-content: flex-start;
        }
        .subject-tag {
            background: #4a7c59;
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 140px;
        }
        .series-progress {
            background: #e8f5e9;
            padding: 4px 10px;
            border-radius: 5px;
            font-size: 0.85em;
            color: #2d5f3f;
            margin-top: 5px;
            display: inline-block;
        }
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin-top: 3px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4caf50, #66bb6a);
            transition: width 0.3s;
        }
        .no-results {
            text-align: center;
            padding: 50px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            color: #4a7c59;
            font-size: 1.2em;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: white;
            font-size: 1.5em;
        }
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
        }
        .modal-header {
            padding: 30px;
            border-bottom: 2px solid #e8f5e9;
            display: flex;
            justify-content: space-between;
        }
        .close-btn {
            background: none;
            border: none;
            font-size: 2em;
            cursor: pointer;
            color: #999;
        }
        .close-btn:hover { color: #2d5f3f; }
        .modal-body { padding: 30px; }
        .list-view {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        .list-view h2 {
            color: #1a4d2e;
            margin-bottom: 20px;
            font-size: 2em;
        }
        .list-item {
            padding: 15px;
            border-bottom: 1px solid #e8f5e9;
            cursor: pointer;
            transition: background 0.3s;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .list-item:hover { background: #e8f5e9; }
        .list-item-covers {
            display: flex;
            gap: 5px;
            flex-shrink: 0;
        }
        .list-item-cover-thumb {
            width: 40px;
            height: 60px;
            border-radius: 3px;
            object-fit: cover;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        .list-item-cover-placeholder {
            width: 40px;
            height: 60px;
            background: linear-gradient(135deg, #2d5f3f 0%, #4a7c59 100%);
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.2em;
        }
        .list-item-info { flex: 1; }
        .list-item-name {
            font-size: 1.2em;
            color: #2d5f3f;
            font-weight: bold;
        }
        .list-item-count { color: #4a7c59; font-size: 0.9em; }
        .back-btn {
            padding: 10px 20px;
            background: #4a7c59;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
        }
        .back-btn:hover { background: #2d5f3f; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 TT's eLibrary</h1>
            <p class="subtitle">Browse and download the eBook collection</p>
            <div class="total-books-badge" id="totalBooksBadge">Loading...</div>
        </header>
        
        <div id="mainView">
            <div class="search-bar">
                <input type="text" class="search-input" id="searchInput" placeholder="Search by title, author, subject, or series...">
                <div class="filters">
                    <button class="filter-btn active" data-filter="all">All Books</button>
                    <button class="filter-btn" data-filter="series">In Series</button>
                    <button class="filter-btn" data-filter="standalone">Standalone</button>
                </div>
                <div class="advanced-filters">
                    <button class="filter-toggle" id="filterRead">✓ Read</button>
                    <button class="filter-toggle" id="filterReading">📖 Currently Reading</button>
                    <button class="filter-toggle" id="filterUnread">📚 Unread</button>
                    <button class="filter-toggle" id="filterOwned">💾 Books I Own</button>
                    <button class="filter-toggle" id="filter5Star">⭐ 5-Star Books</button>
                </div>
            </div>
            <div class="stats">
                <div class="stat-card" onclick="showAuthors()">
                    <div class="stat-number" id="totalAuthors">0</div>
                    <div class="stat-label">Authors</div>
                </div>
                <div class="stat-card" onclick="showSeries()">
                    <div class="stat-number" id="totalSeries">0</div>
                    <div class="stat-label">Series</div>
                </div>
                <div class="stat-card" onclick="showSubjects()">
                    <div class="stat-number" id="totalSubjects">0</div>
                    <div class="stat-label">Subjects</div>
                </div>
            </div>
            <div id="booksContainer">
                <div class="loading">Loading library...</div>
            </div>
        </div>
        
        <div id="listView" style="display: none;">
            <div class="list-view">
                <button class="back-btn" onclick="showMainView()">← Back to Library</button>
                <h2 id="listTitle"></h2>
                <div id="listContainer"></div>
            </div>
        </div>
    </div>
    
    <div id="bookModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div></div>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody">
                <div class="loading">Loading...</div>
            </div>
        </div>
    </div>
    
    <script>
        // State variables
        let allBooks = [];
        let currentFilter = 'all';
        let advancedFilters = { read: false, reading: false, unread: false, owned: false, fivestar: false };
        
        // Helper functions
        function getReadingStatusBadge(book) {
            if (!book.read_status) return '';
            if (book.read_status === 'read') return '<div class="reading-status-badge status-read">✓ Read</div>';
            if (book.read_status === 'currently-reading') return '<div class="reading-status-badge status-reading">📖 Reading</div>';
            if (book.read_status === 'to-read') return '<div class="reading-status-badge status-to-read">📚 To Read</div>';
            return '';
        }
        
        function getStarRating(rating) {
            if (!rating) return '';
            return `<div class="book-rating">${'⭐'.repeat(Math.floor(rating))} ${rating}</div>`;
        }
        
        function getSeriesProgress(book) {
            if (!book.series_progress) return '';
            const percent = (book.series_progress.read / book.series_progress.total) * 100;
            return `<div class="series-progress">${book.series_progress.read}/${book.series_progress.total} books read<div class="progress-bar"><div class="progress-fill" style="width: ${percent}%"></div></div></div>`;
        }
        
        // Load and display books
        async function loadBooks() {
            try {
                const response = await fetch('/api/books');
                const data = await response.json();
                allBooks = data.books;
                displayBooks(allBooks);
                updateStats(data.stats);
                console.log(`Loaded ${allBooks.length} books`);
            } catch (error) {
                document.getElementById('booksContainer').innerHTML = '<div class="no-results">Error loading books</div>';
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
                        ${getReadingStatusBadge(book)}
                        ${book.has_cover ? `<img src="/api/cover/${book.id}" class="book-card-cover">` : '<div class="book-card-cover-placeholder">📚</div>'}
                        <div class="book-card-info">
                            <div class="book-title">${book.title}</div>
                            <div class="book-author">by ${book.authors}</div>
                            ${getStarRating(book.star_rating)}
                            ${book.series ? `<div class="book-series">${book.series}</div>` : ''}
                            ${getSeriesProgress(book)}
                            ${book.subjects.length > 0 ? `<div class="book-subjects">${book.subjects.map(s => `<span class="subject-tag">${s}</span>`).join('')}</div>` : ''}
                        </div>
                    </div>
                `).join('') + '</div>';
        }
        
        // Filter functions
        function toggleAdvancedFilter(filterName) {
            advancedFilters[filterName] = !advancedFilters[filterName];
            const btn = document.getElementById('filter' + filterName.charAt(0).toUpperCase() + filterName.slice(1).replace('star', 'Star'));
            if (btn) btn.classList.toggle('active');
            applyFilters();
        }
        
        function applyFilters() {
            const searchTerm = document.getElementById('searchInput').value;
            let filtered = allBooks;
            
            if (currentFilter === 'series') filtered = filtered.filter(b => b.series);
            if (currentFilter === 'standalone') filtered = filtered.filter(b => !b.series);
            if (advancedFilters.read) filtered = filtered.filter(b => b.read_status === 'read');
            if (advancedFilters.reading) filtered = filtered.filter(b => b.read_status === 'currently-reading');
            if (advancedFilters.unread) filtered = filtered.filter(b => !b.read_status || b.read_status === 'to-read');
            if (advancedFilters.owned) filtered = filtered.filter(b => b.owned);
            if (advancedFilters.fivestar) filtered = filtered.filter(b => b.star_rating >= 5);
            
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                filtered = filtered.filter(b => 
                    b.title.toLowerCase().includes(term) ||
                    b.authors.toLowerCase().includes(term) ||
                    b.subjects.some(s => s.toLowerCase().includes(term)) ||
                    (b.series && b.series.toLowerCase().includes(term))
                );
            }
            
            displayBooks(filtered);
        }
        
        function updateStats(stats) {
            document.getElementById('totalBooksBadge').textContent = `📚 ${stats.total_books} Books in Collection`;
            document.getElementById('totalAuthors').textContent = stats.total_authors;
            document.getElementById('totalSeries').textContent = stats.total_series;
            document.getElementById('totalSubjects').textContent = stats.total_subjects;
        }
        
        async function showBookDetails(bookId) {
            const modal = document.getElementById('bookModal');
            modal.classList.add('active');
            try {
                const response = await fetch(`/api/book/${bookId}`);
                const book = await response.json();
                document.getElementById('modalBody').innerHTML = `<h2>${book.title}</h2><p>by ${book.authors}</p>`;
            } catch (error) {
                document.getElementById('modalBody').innerHTML = '<div class="no-results">Error loading details</div>';
            }
        }
        
        function closeModal() {
            document.getElementById('bookModal').classList.remove('active');
        }
        
        async function showAuthors() {
            document.getElementById('mainView').style.display = 'none';
            document.getElementById('listView').style.display = 'block';
        }
        
        async function showSeries() {
            document.getElementById('mainView').style.display = 'none';
            document.getElementById('listView').style.display = 'block';
        }
        
        async function showSubjects() {
            document.getElementById('mainView').style.display = 'none';
            document.getElementById('listView').style.display = 'block';
        }
        
        function showMainView() {
            document.getElementById('listView').style.display = 'none';
            document.getElementById('mainView').style.display = 'block';
        }
        
        // Event listeners
        document.getElementById('searchInput').addEventListener('input', applyFilters);
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                applyFilters();
            });
        });
        document.getElementById('filterRead').addEventListener('click', () => toggleAdvancedFilter('read'));
        document.getElementById('filterReading').addEventListener('click', () => toggleAdvancedFilter('reading'));
        document.getElementById('filterUnread').addEventListener('click', () => toggleAdvancedFilter('unread'));
        document.getElementById('filterOwned').addEventListener('click', () => toggleAdvancedFilter('owned'));
        document.getElementById('filter5Star').addEventListener('click', () => toggleAdvancedFilter('fivestar'));
        window.onclick = (e) => { if (e.target.id === 'bookModal') closeModal(); };
        
        // Initialize
        loadBooks();
    </script>
</body>
</html>
'''

def get_all_books():
    """Get all books with reading data"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, cover_path FROM books ORDER BY title')
    books = cursor.fetchall()
    
    result = []
    for book_id, title, cover_path in books:
        cursor.execute('SELECT a.author_name FROM authors a JOIN book_authors ba ON a.id = ba.author_id WHERE ba.book_id = ?', (book_id,))
        authors = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('SELECT ser.series_name, bser.series_index FROM series ser JOIN book_series bser ON ser.id = bser.series_id WHERE bser.book_id = ?', (book_id,))
        series_result = cursor.fetchone()
        series = f"{series_result[0]} #{series_result[1]}" if series_result else None
        
        cursor.execute('SELECT s.subject_name FROM subjects s JOIN book_subjects bs ON s.id = bs.subject_id WHERE bs.book_id = ? LIMIT 4', (book_id,))
        subjects = [row[0] for row in cursor.fetchall()]
        
        try:
            cursor.execute('SELECT read_status, star_rating FROM reading_history WHERE book_id = ? OR LOWER(title) = LOWER(?) LIMIT 1', (book_id, title))
            reading_data = cursor.fetchone()
            read_status = reading_data[0] if reading_data else None
            star_rating = reading_data[1] if reading_data else None
        except:
            read_status = None
            star_rating = None
        
        cursor.execute('SELECT COUNT(*) FROM book_files WHERE book_id = ?', (book_id,))
        owned = cursor.fetchone()[0] > 0
        
        has_cover = cover_path and os.path.exists(cover_path)
        
        result.append({
            'id': book_id,
            'title': title,
            'authors': ', '.join(authors) if authors else 'Unknown',
            'series': series,
            'subjects': subjects,
            'has_cover': has_cover,
            'read_status': read_status,
            'star_rating': star_rating,
            'owned': owned,
            'series_progress': None
        })
    
    conn.close()
    return result

def get_stats():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM books')
    total_books = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    total_authors = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM series')
    total_series = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM subjects')
    total_subjects = cursor.fetchone()[0]
    conn.close()
    return {'total_books': total_books, 'total_authors': total_authors, 'total_series': total_series, 'total_subjects': total_subjects}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/books')
def api_books():
    return jsonify({'books': get_all_books(), 'stats': get_stats()})

@app.route('/api/book/<int:book_id>')
def api_book_details(book_id):
    return jsonify({'id': book_id, 'title': 'Book', 'authors': 'Author'})

@app.route('/api/cover/<int:book_id>')
def api_cover(book_id):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT cover_path FROM books WHERE id = ?', (book_id,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0])
    return '', 404

if __name__ == '__main__':
    if not DB_PATH.exists():
        print(f"Error: Database not found: {DB_PATH}")
    else:
        print("="*60)
        print("TT's eLibrary - Starting...")
        print("http://localhost:5000")
        print("="*60)
        app.run(host='0.0.0.0', port=5000, debug=True)