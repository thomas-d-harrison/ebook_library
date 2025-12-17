# 📚 ebook library system
> A powerful Python-based ebook processing system with web interface

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![SQLite](https://img.shields.io/badge/sqlite-3-yellow.svg)

## 🐍 Prerequisites

**Python 3.8+** is required. Don't have Python? 

[![](https://img.shields.io/badge/Download-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)

**eBook files** are required. Need files?

[![](https://img.shields.io/badge/Google_Drive-4285F4?style=for-the-badge&logo=googledrive&logoColor=white&logoSize=auto)](https://drive.google.com/file/d/1QWVho6HJ2GJiDLe13RqqBcv1zJX2V4VC/view?usp=sharing) 

## 📁 Project Structure
```
Library/
├── 📂 infra/        # Database files - Home to ebook_processor.py, the code to build infrastructure and ingest ebook data into a new db.
├── 📂 utils/        # Utility scripts - Functionality includes deletion of deuplicate folders, book series viewer, and SQL queries.
├── 📂 debug/        # Debugging scripts - Any code to debug, test, troubleshoot, and explore this ebook library system.
└── 📂 tt lib/       # eBook files - Where to extract tt lib root or place your root.
```
## ✨ Features

- 📖 **Catalog Management** - Organize your entire ebook collection
- 🔍 **Smart Search** - Find books by title, author, or genre
- 📊 **Series Tracking** - Keep track of book series and reading order
- 🎨 **Cover Wall** - Beautiful visual grid of all your book covers
- 🌐 **Web Interface** - Access your library from any device
- ⬇️ **Downloads** - Direct download to any device


## 🚀 Quick Start
```bash
# Install dependencies
py -m pip install flask

# Run the cataloger
python ebook_cataloger.py

# Start web server
python library_web_server.py
```

## 💡 Usage

### Catalog Your Books
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
``
Open `http://localhost:5000``

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Metadata:** OPF/XML parsing

## 📝 License

MIT License - feel free to use for your own library!
