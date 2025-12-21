from flask import Flask, render_template, jsonify, send_file
import sqlite3
import os
from pathlib import Path

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent

app = Flask(__name__, 
            template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))

DB_PATH = BASE_DIR / '..' / 'infra' / 'data' / 'tt_db_ebook_lib.db'

def get_all_books():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, cover_path FROM books ORDER BY title')
    books = cursor.fetchall()
    result = []
    for book_id, title, cover_path in books:
        cursor.execute('SELECT a.author_name, a.author_sort FROM authors a JOIN book_authors ba ON a.id = ba.author_id WHERE ba.book_id = ?', (book_id,))
        author_data = cursor.fetchall()
        authors = [row[0] for row in author_data]
        author_sort = author_data[0][1] if author_data and author_data[0][1] else (authors[0] if authors else 'Unknown')
        cursor.execute('SELECT ser.series_name, bser.series_index FROM series ser JOIN book_series bser ON ser.id = bser.series_id WHERE bser.book_id = ?', (book_id,))
        series_result = cursor.fetchone()
        series = f"{series_result[0]} #{series_result[1]}" if series_result else None
        cursor.execute('SELECT s.subject_name FROM subjects s JOIN book_subjects bs ON s.id = bs.subject_id WHERE bs.book_id = ? LIMIT 4', (book_id,))
        subjects = [row[0] for row in cursor.fetchall()]
        has_cover = cover_path is not None and os.path.exists(cover_path)
        result.append({'id': book_id, 'title': title, 'authors': ', '.join(authors) if authors else 'Unknown', 'author_sort': author_sort, 'series': series, 'subjects': subjects, 'has_cover': has_cover})
    conn.close()
    return result

def get_book_details(book_id):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book_row = cursor.fetchone()
    if not book_row:
        conn.close()
        return None
    cursor.execute('SELECT a.author_name FROM authors a JOIN book_authors ba ON a.id = ba.author_id WHERE ba.book_id = ?', (book_id,))
    authors = [row[0] for row in cursor.fetchall()]
    cursor.execute('SELECT ser.series_name, bser.series_index FROM series ser JOIN book_series bser ON ser.id = bser.series_id WHERE bser.book_id = ?', (book_id,))
    series_result = cursor.fetchone()
    series = f"{series_result[0]} #{series_result[1]}" if series_result else None
    cursor.execute('SELECT s.subject_name FROM subjects s JOIN book_subjects bs ON s.id = bs.subject_id WHERE bs.book_id = ?', (book_id,))
    subjects = [row[0] for row in cursor.fetchall()]
    cursor.execute('SELECT id, file_path, file_format FROM book_files WHERE book_id = ?', (book_id,))
    files = [{'id': row[0], 'path': row[1], 'format': row[2].replace('.', '')} for row in cursor.fetchall()]
    conn.close()
    return {
        'id': book_row[0], 'title': book_row[1], 'authors': ', '.join(authors) if authors else 'Unknown',
        'isbn': book_row[3], 'publisher': book_row[4], 'publish_date': book_row[5],
        'description': book_row[7], 'cover_path': book_row[8], 'series': series,
        'subjects': subjects, 'files': files
    }

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

def get_all_authors_with_counts():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT a.author_name, COUNT(DISTINCT ba.book_id) as book_count FROM authors a JOIN book_authors ba ON a.id = ba.author_id GROUP BY a.author_name ORDER BY a.author_name')
    authors = cursor.fetchall()
    result = []
    for author_name, book_count in authors:
        cursor.execute('SELECT b.id, b.title, b.cover_path FROM books b JOIN book_authors ba ON b.id = ba.book_id JOIN authors a ON ba.author_id = a.id WHERE a.author_name = ? LIMIT 4', (author_name,))
        covers = []
        for book_id, title, cover_path in cursor.fetchall():
            has_cover = cover_path is not None and os.path.exists(cover_path)
            covers.append({'book_id': book_id, 'title': title, 'has_cover': has_cover})
        result.append({'name': author_name, 'book_count': book_count, 'covers': covers})
    conn.close()
    return result

def get_all_series_with_counts():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT s.series_name, COUNT(DISTINCT bs.book_id) as book_count FROM series s JOIN book_series bs ON s.id = bs.series_id GROUP BY s.series_name ORDER BY s.series_name')
    series_list = cursor.fetchall()
    result = []
    for series_name, book_count in series_list:
        cursor.execute('SELECT b.id, b.title, b.cover_path FROM books b JOIN book_series bs ON b.id = bs.book_id JOIN series s ON bs.series_id = s.id WHERE s.series_name = ? ORDER BY bs.series_index LIMIT 4', (series_name,))
        covers = []
        for book_id, title, cover_path in cursor.fetchall():
            has_cover = cover_path is not None and os.path.exists(cover_path)
            covers.append({'book_id': book_id, 'title': title, 'has_cover': has_cover})
        result.append({'name': series_name, 'book_count': book_count, 'covers': covers})
    conn.close()
    return result

def get_all_subjects_with_counts():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT s.subject_name, COUNT(DISTINCT bs.book_id) as book_count FROM subjects s JOIN book_subjects bs ON s.id = bs.subject_id GROUP BY s.subject_name ORDER BY s.subject_name')
    result = [{'name': row[0], 'book_count': row[1]} for row in cursor.fetchall()]
    conn.close()
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/books')
def api_books():
    books = get_all_books()
    stats = get_stats()
    return jsonify({'books': books, 'stats': stats})

@app.route('/api/authors')
def api_authors():
    return jsonify(get_all_authors_with_counts())

@app.route('/api/authors-with-covers')
def api_authors_with_covers():
    return jsonify(get_all_authors_with_counts())

@app.route('/api/series')
def api_series():
    return jsonify(get_all_series_with_counts())

@app.route('/api/series-with-covers')
def api_series_with_covers():
    return jsonify(get_all_series_with_counts())

@app.route('/api/subjects')
def api_subjects():
    return jsonify(get_all_subjects_with_counts())

@app.route('/api/book/<int:book_id>')
def api_book_details(book_id):
    book = get_book_details(book_id)
    if book:
        return jsonify(book)
    return jsonify({'error': 'Book not found'}), 404

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

@app.route('/api/download/<int:file_id>')
def api_download(file_id):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM book_files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0], as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    if not DB_PATH.exists():
        print(f"Error: Database file not found: {DB_PATH}")
        print("Make sure tt_db_ebook_lib.db is in the ../infra/data/ folder.")
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