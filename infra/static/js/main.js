let allBooks = [];
let currentFilter = 'all';
let currentSort = 'title-asc';

async function loadBooks() {
    try {
        const response = await fetch('/api/books');
        const data = await response.json();
        allBooks = data.books;
        displayBooks(allBooks);
        updateStats(data.stats);
    } catch (error) {
        document.getElementById('booksContainer').innerHTML = '<div class="no-results">Error loading books</div>';
    }
}

function sortBooks(books, sortType) {
    const sorted = [...books];
    switch(sortType) {
        case 'title-asc':
            return sorted.sort((a, b) => a.title.localeCompare(b.title));
        case 'title-desc':
            return sorted.sort((a, b) => b.title.localeCompare(a.title));
        case 'author-asc':
            return sorted.sort((a, b) => a.author_sort.localeCompare(b.author_sort));
        case 'author-desc':
            return sorted.sort((a, b) => b.author_sort.localeCompare(a.author_sort));
        case 'recent':
            return sorted.reverse();
        default:
            return sorted;
    }
}

function displayBooks(books) {
    const container = document.getElementById('booksContainer');
    if (books.length === 0) {
        container.innerHTML = '<div class="no-results">No books found</div>';
        return;
    }
    const sortedBooks = sortBooks(books, currentSort);
    container.innerHTML = '<div class="books-grid">' + sortedBooks.map(book => `
        <div class="book-card" onclick="showBookDetails(${book.id})">
            ${book.has_cover ? `<img src="/api/cover/${book.id}" class="book-card-cover">` : `<div class="book-card-cover-placeholder">📚</div>`}
            <div class="book-card-info">
                <div class="book-title">${book.title}</div>
                <div class="book-author">by ${book.authors}</div>
                ${book.series ? `<div class="book-series">${book.series}</div>` : ''}
                ${book.subjects.length > 0 ? `<div class="book-subjects">${book.subjects.map(s => `<span class="subject-tag">${s}</span>`).join('')}</div>` : ''}
            </div>
        </div>
    `).join('') + '</div>';
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
                <div>${book.cover_path ? `<img src="/api/cover/${bookId}" class="book-cover">` : `<div class="book-cover-placeholder">📚</div>`}</div>
                <div class="book-info">
                    <h2>${book.title}</h2>
                    <div class="author">${book.authors}</div>
                    ${book.series ? `<div class="info-row"><div class="info-label">Series</div><div class="info-value">${book.series}</div></div>` : ''}
                    ${book.publisher ? `<div class="info-row"><div class="info-label">Publisher</div><div class="info-value">${book.publisher}</div></div>` : ''}
                    ${book.publish_date ? `<div class="info-row"><div class="info-label">Published</div><div class="info-value">${book.publish_date}</div></div>` : ''}
                    ${book.isbn ? `<div class="info-row"><div class="info-label">ISBN</div><div class="info-value">${book.isbn}</div></div>` : ''}
                </div>
            </div>
            ${book.subjects.length > 0 ? `<div class="info-row"><div class="info-label">Subjects</div><div class="book-subjects">${book.subjects.map(s => `<span class="subject-tag">${s}</span>`).join('')}</div></div>` : ''}
            ${book.description ? `<div class="info-row"><div class="info-label">Description</div><div class="description">${book.description}</div></div>` : ''}
            ${book.files.length > 0 ? `<div class="download-section"><div class="info-label">Download Book</div>${book.files.map(file => `<a href="/api/download/${file.id}" class="download-btn" download>Download <span class="format-badge">${file.format.toUpperCase()}</span></a>`).join('')}</div>` : ''}
        `;
    } catch (error) {
        modalBody.innerHTML = '<div class="no-results">Error loading book details</div>';
    }
}

function closeModal() {
    document.getElementById('bookModal').classList.remove('active');
}

window.onclick = function(event) {
    if (event.target === document.getElementById('bookModal')) closeModal();
}

function filterBooks(searchTerm, filterType) {
    let filtered = allBooks;
    if (filterType === 'series') filtered = filtered.filter(book => book.series !== null);
    else if (filterType === 'standalone') filtered = filtered.filter(book => book.series === null);
    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter(book => 
            book.title.toLowerCase().includes(term) ||
            book.authors.toLowerCase().includes(term) ||
            book.subjects.some(s => s.toLowerCase().includes(term)) ||
            (book.series && book.series.toLowerCase().includes(term))
        );
    }
    displayBooks(filtered);
}

function updateStats(stats) {
    document.getElementById('totalBooksBadge').textContent = `📖 ${stats.total_books} Books`;
}

async function showAuthors() {
    try {
        const response = await fetch('/api/authors-with-covers');
        const allAuthors = await response.json();
        document.getElementById('mainView').style.display = 'none';
        document.getElementById('listView').style.display = 'block';
        document.getElementById('listTitle').textContent = 'All Authors';
        document.getElementById('listContainer').innerHTML = allAuthors.map(author => `
            <div class="list-item" onclick="filterByAuthor('${author.name.replace(/'/g, "\\'")}')">
                <div class="list-item-covers">
                    ${author.covers.slice(0, 4).map(cover => cover.has_cover ? `<img src="/api/cover/${cover.book_id}" class="list-item-cover-thumb">` : `<div class="list-item-cover-placeholder">📚</div>`).join('')}
                </div>
                <div class="list-item-info">
                    <div class="list-item-name">${author.name}</div>
                    <div class="list-item-count">${author.book_count} book${author.book_count !== 1 ? 's' : ''}</div>
                </div>
            </div>
        `).join('');
    } catch (error) { console.error('Error loading authors:', error); }
}

async function showSeries() {
    try {
        const response = await fetch('/api/series-with-covers');
        const allSeries = await response.json();
        document.getElementById('mainView').style.display = 'none';
        document.getElementById('listView').style.display = 'block';
        document.getElementById('listTitle').textContent = 'All Series';
        document.getElementById('listContainer').innerHTML = allSeries.map(series => `
            <div class="list-item" onclick="filterBySeries('${series.name.replace(/'/g, "\\'")}')">
                <div class="list-item-covers">
                    ${series.covers.slice(0, 4).map(cover => cover.has_cover ? `<img src="/api/cover/${cover.book_id}" class="list-item-cover-thumb">` : `<div class="list-item-cover-placeholder">📚</div>`).join('')}
                </div>
                <div class="list-item-info">
                    <div class="list-item-name">${series.name}</div>
                    <div class="list-item-count">${series.book_count} book${series.book_count !== 1 ? 's' : ''}</div>
                </div>
            </div>
        `).join('');
    } catch (error) { console.error('Error loading series:', error); }
}

function showMainView() {
    document.getElementById('listView').style.display = 'none';
    document.getElementById('mainView').style.display = 'block';
    document.getElementById('searchInput').value = '';
    filterBooks('', 'all');
}

function showAllBooks() {
    showMainView();
    document.getElementById('searchInput').focus();
}

function filterByAuthor(authorName) {
    showMainView();
    document.getElementById('searchInput').value = authorName;
    filterBooks(authorName, currentFilter);
}

function filterBySeries(seriesName) {
    showMainView();
    document.getElementById('searchInput').value = seriesName;
    filterBooks(seriesName, currentFilter);
}

document.getElementById('searchInput').addEventListener('input', (e) => filterBooks(e.target.value, currentFilter));

document.getElementById('sortSelect').addEventListener('change', (e) => {
    currentSort = e.target.value;
    filterBooks(document.getElementById('searchInput').value, currentFilter);
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