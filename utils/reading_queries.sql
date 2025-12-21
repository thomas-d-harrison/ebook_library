-- Get all books you've read with ratings
SELECT 
    rh.title,
    rh.authors,
    rh.star_rating,
    rh.last_date_read,
    rh.review
FROM reading_history rh
WHERE rh.read_status = 'read'
ORDER BY rh.star_rating DESC;

-- Books you own vs books you've read
SELECT 
    b.title,
    a.author_name,
    CASE WHEN rh.id IS NOT NULL THEN 'Read' ELSE 'Unread' END as read_status,
    rh.star_rating
FROM books b
JOIN book_authors ba ON b.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
LEFT JOIN reading_history rh ON b.id = rh.book_id
ORDER BY b.title;

-- Reading statistics by author
SELECT 
    rh.authors,
    COUNT(*) as books_read,
    AVG(rh.star_rating) as avg_rating,
    MAX(rh.star_rating) as highest_rating
FROM reading_history rh
WHERE rh.read_status = 'read'
GROUP BY rh.authors
ORDER BY books_read DESC;

-- Books to read that you own
SELECT 
    b.title,
    a.author_name,
    s.series_name,
    bser.series_index
FROM books b
JOIN book_authors ba ON b.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_series bser ON b.id = bser.book_id
LEFT JOIN series s ON bser.series_id = s.id
LEFT JOIN reading_history rh ON b.id = rh.book_id
WHERE rh.read_status IS NULL OR rh.read_status = 'to-read'
ORDER BY a.author_name, s.series_name, bser.series_index;

-- Reading pace over time
SELECT 
    strftime('%Y-%m', last_date_read) as month,
    COUNT(*) as books_finished
FROM reading_history
WHERE read_status = 'read' 
  AND last_date_read IS NOT NULL
GROUP BY strftime('%Y-%m', last_date_read)
ORDER BY month DESC;

-- Books with specific moods
SELECT 
    rh.title,
    rh.authors,
    rh.star_rating,
    ba.moods,
    ba.pace
FROM reading_history rh
JOIN book_attributes ba ON rh.id = ba.reading_history_id
WHERE ba.moods LIKE '%dark%'
   OR ba.moods LIKE '%mysterious%'
ORDER BY rh.star_rating DESC;

-- Your highest rated series
SELECT 
    s.series_name,
    COUNT(*) as books_in_series,
    AVG(rh.star_rating) as avg_rating
FROM reading_history rh
JOIN books b ON rh.book_id = b.id
JOIN book_series bser ON b.id = bser.book_id
JOIN series s ON bser.series_id = s.id
WHERE rh.star_rating IS NOT NULL
GROUP BY s.series_name
HAVING COUNT(*) >= 2
ORDER BY avg_rating DESC;

-- Books you re-read (read count > 1)
SELECT 
    title,
    authors,
    read_count,
    star_rating,
    dates_read
FROM reading_history
WHERE read_count > 1
ORDER BY read_count DESC;

-- Content warnings summary
SELECT 
    cw.warning_text,
    COUNT(*) as book_count
FROM content_warnings cw
WHERE cw.warning_text IS NOT NULL AND cw.warning_text != ''
GROUP BY cw.warning_text
ORDER BY book_count DESC;

-- Books with strong character development
SELECT 
    rh.title,
    rh.authors,
    rh.star_rating,
    ba.strong_character_dev,
    ba.loveable_characters,
    ba.diverse_characters
FROM reading_history rh
JOIN book_attributes ba ON rh.id = ba.reading_history_id
WHERE ba.strong_character_dev = 'Yes'
ORDER BY rh.star_rating DESC;


select * from reading_history;
select * from books;
select * from book_attributes;

select * from tt_db_ebook_lib.information_schema.tables;