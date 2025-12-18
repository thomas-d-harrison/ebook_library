-- ========================================
-- BASIC BOOK QUERIES
-- ========================================

-- Get a book with all its authors
SELECT 
    b.id,
    b.title,
    b.isbn,
    b.publisher,
    b.publish_date,
    GROUP_CONCAT(a.author_name) as authors
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
--WHERE b.id = 1
GROUP BY b.id;

-- Get a book with all its subjects
SELECT 
    b.id,
    b.title,
    GROUP_CONCAT(s.subject_name, ', ') as subjects
FROM books b
LEFT JOIN book_subjects bs ON b.id = bs.book_id
LEFT JOIN subjects s ON bs.subject_id = s.id
WHERE b.id = 1
GROUP BY b.id;

-- Get complete book details (authors, subjects, files)
SELECT 
    b.id,
    b.title,
    b.isbn,
    b.publisher,
    b.publish_date,
    b.language,
    b.description,
    GROUP_CONCAT(DISTINCT a.author_name) as authors,
    GROUP_CONCAT(DISTINCT s.subject_name) as subjects,
    GROUP_CONCAT(DISTINCT bf.file_format) as available_formats,
    COUNT(DISTINCT bf.id) as format_count
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_subjects bs ON b.id = bs.book_id
LEFT JOIN subjects s ON bs.subject_id = s.id
LEFT JOIN book_files bf ON b.id = bf.book_id
WHERE b.id = 1
GROUP BY b.id;

-- ========================================
-- FORMAT QUERIES
-- ========================================

-- Count how many formats each book has
SELECT 
    b.id,
    b.title,
    COUNT(bf.id) as format_count,
    GROUP_CONCAT(bf.file_format, ', ') as formats
FROM books b
LEFT JOIN book_files bf ON b.id = bf.book_id
GROUP BY b.id
ORDER BY format_count DESC;

-- Find books with specific format (e.g., EPUB)
SELECT 
    b.id,
    b.title,
    GROUP_CONCAT(a.author_name, ', ') as authors,
    bf.file_path
FROM books b
JOIN book_files bf ON b.id = bf.book_id
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
WHERE bf.file_format = '.epub'
GROUP BY b.id;

-- Find books with multiple formats
SELECT 
    b.id,
    b.title,
    COUNT(bf.id) as format_count,
    GROUP_CONCAT(bf.file_format, ', ') as formats
FROM books b
JOIN book_files bf ON b.id = bf.book_id
GROUP BY b.id
HAVING COUNT(bf.id) > 1;

-- ========================================
-- AUTHOR QUERIES
-- ========================================

-- Get all books by a specific author
SELECT 
    b.id,
    b.title,
    b.publish_date,
    GROUP_CONCAT(DISTINCT a2.author_name) as all_authors
FROM books b
JOIN book_authors ba ON b.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_authors ba2 ON b.id = ba2.book_id
LEFT JOIN authors a2 ON ba2.author_id = a2.id
WHERE a.author_name = 'J. R. R. Tolkien'
GROUP BY b.id
ORDER BY b.publish_date;

-- Count books per author
SELECT 
    a.author_name,
    COUNT(DISTINCT ba.book_id) as book_count
FROM authors a
LEFT JOIN book_authors ba ON a.id = ba.author_id
GROUP BY a.id
ORDER BY book_count DESC;

-- Find co-authored books (books with multiple authors)
SELECT 
    b.id,
    b.title,
    COUNT(ba.author_id) as author_count,
    GROUP_CONCAT(a.author_name, ' & ') as authors
FROM books b
JOIN book_authors ba ON b.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
GROUP BY b.id
HAVING COUNT(ba.author_id) > 1;

-- ========================================
-- SUBJECT QUERIES
-- ========================================

-- Get all books in a specific subject
SELECT 
    b.id,
    b.title,
    GROUP_CONCAT(DISTINCT a.author_name) as authors
FROM books b
JOIN book_subjects bs ON b.id = bs.book_id
JOIN subjects s ON bs.subject_id = s.id
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
WHERE s.subject_name = 'Fantasy'
GROUP BY b.id
ORDER BY a.author_name;

-- Count books per subject
SELECT 
    s.subject_name,
    COUNT(DISTINCT bs.book_id) as book_count
FROM subjects s
LEFT JOIN book_subjects bs ON s.id = bs.subject_id
GROUP BY s.id
ORDER BY book_count DESC;

-- Find books with multiple subjects
SELECT 
    b.id,
    b.title,
    COUNT(bs.subject_id) as subject_count,
    GROUP_CONCAT(s.subject_name) as subjects
FROM books b
LEFT JOIN book_subjects bs ON b.id = bs.book_id
LEFT JOIN subjects s ON bs.subject_id = s.id
GROUP BY b.id
HAVING COUNT(bs.subject_id) > 1;

-- ========================================
-- SEARCH QUERIES
-- ========================================

-- Full-text search across title, author, and subject
SELECT DISTINCT
    b.id,
    b.title,
    GROUP_CONCAT(DISTINCT a.author_name, ', ') as authors,
    GROUP_CONCAT(DISTINCT s.subject_name, ', ') as subjects
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_subjects bs ON b.id = bs.book_id
LEFT JOIN subjects s ON bs.subject_id = s.id
WHERE 
    b.title LIKE '%search_term%'
    OR a.author_name LIKE '%search_term%'
    OR s.subject_name LIKE '%search_term%'
    OR b.description LIKE '%search_term%'
GROUP BY b.id;

-- Advanced search with multiple filters
SELECT DISTINCT
    b.id,
    b.title,
    GROUP_CONCAT(DISTINCT a.author_name, ', ') as authors,
    b.publish_date
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_subjects bs ON b.id = bs.book_id
LEFT JOIN subjects s ON bs.subject_id = s.id
LEFT JOIN book_files bf ON b.id = bf.book_id
WHERE 
    (b.title LIKE '%fantasy%' OR s.subject_name LIKE '%fantasy%')
    AND bf.file_format = '.epub'
    AND b.language = 'en'
GROUP BY b.id;

-- ========================================
-- STATISTICS QUERIES
-- ========================================

-- Library statistics overview
SELECT 
    (SELECT COUNT(*) FROM books) as total_books,
    (SELECT COUNT(*) FROM authors) as total_authors,
    (SELECT COUNT(*) FROM subjects) as total_subjects,
    (SELECT COUNT(*) FROM book_files) as total_files,
    (SELECT SUM(file_size) FROM book_files) as total_size_bytes,
    (SELECT ROUND(SUM(file_size) / 1024.0 / 1024.0 / 1024.0, 2) FROM book_files) as total_size_gb;

-- Books by language
SELECT 
    language,
    COUNT(*) as book_count
FROM books
WHERE language IS NOT NULL
GROUP BY language
ORDER BY book_count DESC;

-- Books by publisher
SELECT 
    publisher,
    COUNT(*) as book_count
FROM books
WHERE publisher IS NOT NULL
GROUP BY publisher
ORDER BY book_count DESC
LIMIT 10;

-- Books by year
SELECT 
    SUBSTR(publish_date, 1, 4) as year,
    COUNT(*) as book_count
FROM books
WHERE publish_date IS NOT NULL
GROUP BY year
ORDER BY year DESC;

-- ========================================
-- UTILITY QUERIES
-- ========================================

-- Find books missing metadata
SELECT 
    b.id,
    b.title,
    CASE WHEN b.isbn IS NULL THEN 'Missing ISBN' ELSE '' END as isbn_status,
    CASE WHEN b.publisher IS NULL THEN 'Missing Publisher' ELSE '' END as publisher_status,
    CASE WHEN b.description IS NULL THEN 'Missing Description' ELSE '' END as desc_status,
    CASE WHEN b.cover_path IS NULL THEN 'Missing Cover' ELSE '' END as cover_status
FROM books b
WHERE 
    b.isbn IS NULL 
    OR b.publisher IS NULL 
    OR b.description IS NULL 
    OR b.cover_path IS NULL;

-- Find duplicate books (same title and author)
SELECT 
    b1.title,
    GROUP_CONCAT(DISTINCT a.author_name) as authors,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(b1.id) as book_ids
FROM books b1
JOIN books b2 ON b1.title = b2.title AND b1.id < b2.id
JOIN book_authors ba ON b1.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
GROUP BY b1.title
HAVING COUNT(*) > 1;

-- Recent additions
SELECT 
    b.id,
    b.title,
    GROUP_CONCAT(DISTINCT a.author_name, ', ') as authors,
    b.created_at
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
GROUP BY b.id
ORDER BY b.created_at DESC
LIMIT 20;