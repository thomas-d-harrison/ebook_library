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

## 📁 Project Structure
```
Library/
├── 📂 infra/        # Database files - Home to ebook_processor.py, the code to build infrastructure and ingest ebook data into a new db.
├── 📂 utils/        # Utility scripts - Functionality includes deletion of deuplicate folders, book series viewer, and SQL queries.
├── 📂 debug/        # Debugging scripts - Any code to debug, test, troubleshoot, and explore this ebook library system.
└── 📂 tt lib/       # eBook files - Where to extract tt lib root or place your root.

## 🚀 Quick Start
```bash
# Install dependencies
py -m pip install flask

# Run the cataloger
python ebook_processor.py

# Start web server
python library_web_server.py
```

## 💡 Usage

### Process Your Books
```bash
python ebook_processor.py
```

### Browse Your Library
```bash
python library_web_server.py
```
Open `http://localhost:5000`

### View Cover Wall
```bash
python cover_wall_view.py
```
Open `http://localhost:5000`

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Metadata:** OPF/XML parsing

## 📝 License

MIT License

Copyright (c) 2025 Thomas Harrison

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
