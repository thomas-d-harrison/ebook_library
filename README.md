# 📚 ebook library system
> A Python-based eBook processing system with web interface

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![SQLite](https://img.shields.io/badge/sqlite-3-yellow.svg)


## 🐍 Prerequisites

**Python 3.8+** is required. Don't have Python? 

[![](https://img.shields.io/badge/Download-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)

**eBook files** are required. Need files?

[![](https://img.shields.io/badge/Google_Drive-4285F4?style=for-the-badge&logo=googledrive&logoColor=white&logoSize=auto)](https://drive.google.com/file/d/1QWVho6HJ2GJiDLe13RqqBcv1zJX2V4VC/view?usp=sharing) 

```
## ✨ Features

- 📖 **Catalog Management** - Organize your entire ebook collection
- 🔍 **Smart Search** - Find books by title, author, or genre
- 📊 **Series Tracking** - Keep track of book series and reading order
- 🎨 **Cover Wall** - Beautiful visual grid of all your book covers
- 🌐 **Web Interface** - Access your library from any device
- ⬇️ **Downloads** - Direct download to any device
- 📈 **Reading History (StoryGraph)** - Import reading progress, ratings, and reviews

---

## 📁 Project Structure

```
Library/
├── 📂 infra/        # Database files and processors (ebook + StoryGraph)
│   ├── ebook_processor.py           # Builds DB + ingests ebook metadata
│   └── storygraph_processor.py      # Imports StoryGraph CSV reading history
├── 📂 utils/        # Utility scripts (dedupe folders, series viewer, SQL helpers)
├── 📂 debug/        # Debugging / exploration scripts
├── 📂 tt lib/       # eBook files (extract or place your library root here)
└── 📂 data/         # CSV exports (StoryGraph)
```

---

## 🚀 Quick Start

```bash
# Install dependencies
py -m pip install flask

# Build ebook catalog database
python ebook_processor.py

# (Optional) Import StoryGraph reading history
python storygraph_processor.py

# Start web server
python library_web_server.py
```

---

## 💡 Usage

### 1️⃣ Process Your Books

Builds the core ebook catalog (books, authors, series, metadata):

```bash
python ebook_processor.py
```

### 2️⃣ Import StoryGraph Reading History

Imports your StoryGraph CSV export and links it to existing books when possible.

**Steps:**

1. Export your data from StoryGraph (CSV)
2. Place the CSV file in the same directory as `storygraph_processor.py`
3. Run:

```bash
python storygraph_processor.py
```

**What gets imported:**

- Reading status (Read / Currently Reading / To Read)
- Dates read
- Read counts
- Star ratings
- Reviews
- Moods & reading attributes
- Content warnings

Data is stored in:

- `reading_history`
- `book_attributes`
- `content_warnings`

### 3️⃣ Browse Your Library

```bash
python library_web_server.py
```

Open: `http://localhost:5000`

### 4️⃣ View Cover Wall

```bash
python cover_wall_view.py
```

Open: `http://localhost:5000`

---

## 🧠 Data Model Notes

- Ebook metadata is treated as the **source of truth** for books and authors
- StoryGraph data is imported as **reading history**, not book definitions
- Reading history optionally links to existing books via title/author matching
- If no match is found, reading history is still preserved

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Metadata:** OPF/XML parsing, CSV ingestion

---

## 📝 License

MIT License

Copyright (c) 2025 Thomas Harrison

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
