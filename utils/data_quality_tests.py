import sqlite3
from pathlib import Path
from collections import Counter
import os

class DataQualityChecker:
    def __init__(self, db_path='../infra/data/tt_db_ebook_lib.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def connect(self):
        """Connect to SQLite database"""
        if not os.path.exists(self.db_path):
            print(f"❌ ERROR: Database not found at {self.db_path}")
            return False
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to database: {self.db_path}\n")
        return True
    
    def log_issue(self, test_name, severity, message, details=None):
        """Log a data quality issue"""
        issue = {
            'test': test_name,
            'severity': severity,  # 'ERROR', 'WARNING', 'INFO'
            'message': message,
            'details': details
        }
        if severity == 'ERROR':
            self.issues.append(issue)
        elif severity == 'WARNING':
            self.warnings.append(issue)
    
    def print_separator(self, title):
        """Print a formatted separator"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    
    # ============================================================================
    # TEST 1: Check for Missing Critical Data
    # ============================================================================
    def test_missing_titles(self):
        """Check for books without titles"""
        self.cursor.execute("SELECT id, book_folder FROM books WHERE title IS NULL OR title = ''")
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Missing Titles',
                'ERROR',
                f'Found {len(results)} books without titles',
                [f"Book ID {r[0]}: {r[1]}" for r in results[:10]]
            )
        return len(results)
    
    def test_missing_authors(self):
        """Check for books without authors"""
        self.cursor.execute('''
            SELECT b.id, b.title, b.book_folder 
            FROM books b
            LEFT JOIN book_authors ba ON b.id = ba.book_id
            WHERE ba.book_id IS NULL
        ''')
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Missing Authors',
                'WARNING',
                f'Found {len(results)} books without authors',
                [f"Book ID {r[0]}: {r[1]}" for r in results[:10]]
            )
        return len(results)
    
    def test_missing_files(self):
        """Check for books without any file attachments"""
        self.cursor.execute('''
            SELECT b.id, b.title, b.book_folder 
            FROM books b
            LEFT JOIN book_files bf ON b.id = bf.book_id
            WHERE bf.book_id IS NULL
        ''')
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Missing Files',
                'ERROR',
                f'Found {len(results)} books without any file attachments',
                [f"Book ID {r[0]}: {r[1]}" for r in results[:10]]
            )
        return len(results)
    
    # ============================================================================
    # TEST 2: Check File System Integrity
    # ============================================================================
    def test_missing_book_folders(self):
        """Check if book folders actually exist on disk"""
        self.cursor.execute("SELECT id, title, book_folder FROM books")
        results = self.cursor.fetchall()
        
        missing = []
        for book_id, title, folder in results:
            if folder and not os.path.exists(folder):
                missing.append((book_id, title, folder))
        
        if missing:
            self.log_issue(
                'Missing Book Folders',
                'ERROR',
                f'Found {len(missing)} books with missing folders on disk',
                [f"Book ID {m[0]}: {m[1]} -> {m[2]}" for m in missing[:10]]
            )
        return len(missing)
    
    def test_missing_cover_files(self):
        """Check if cover image files exist on disk"""
        self.cursor.execute("SELECT id, title, cover_path FROM books WHERE cover_path IS NOT NULL")
        results = self.cursor.fetchall()
        
        missing = []
        for book_id, title, cover_path in results:
            if not os.path.exists(cover_path):
                missing.append((book_id, title, cover_path))
        
        if missing:
            self.log_issue(
                'Missing Cover Files',
                'WARNING',
                f'Found {len(missing)} books with missing cover files',
                [f"Book ID {m[0]}: {m[1]}" for m in missing[:10]]
            )
        return len(missing)
    
    def test_missing_ebook_files(self):
        """Check if ebook files exist on disk"""
        self.cursor.execute("SELECT bf.id, b.title, bf.file_path FROM book_files bf JOIN books b ON bf.book_id = b.id")
        results = self.cursor.fetchall()
        
        missing = []
        for file_id, title, file_path in results:
            if not os.path.exists(file_path):
                missing.append((file_id, title, file_path))
        
        if missing:
            self.log_issue(
                'Missing eBook Files',
                'ERROR',
                f'Found {len(missing)} ebook files missing from disk',
                [f"File ID {m[0]}: {m[1]} -> {m[2]}" for m in missing[:10]]
            )
        return len(missing)
    
    # ============================================================================
    # TEST 3: Check for Duplicates
    # ============================================================================
    def test_duplicate_books(self):
        """Check for potential duplicate books (same title and author)"""
        self.cursor.execute('''
            SELECT b.title, GROUP_CONCAT(a.author_name), COUNT(*) as cnt, GROUP_CONCAT(b.id)
            FROM books b
            JOIN book_authors ba ON b.id = ba.book_id
            JOIN authors a ON ba.author_id = a.id
            GROUP BY b.title, a.author_name
            HAVING cnt > 1
        ''')
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Duplicate Books',
                'WARNING',
                f'Found {len(results)} potential duplicate books (same title + author)',
                [f"{r[0]} by {r[1]} - {r[2]} copies (IDs: {r[3]})" for r in results[:10]]
            )
        return len(results)
    
    def test_duplicate_authors(self):
        """Check for duplicate author entries with slight variations"""
        self.cursor.execute("SELECT author_name FROM authors ORDER BY author_name")
        authors = [row[0] for row in self.cursor.fetchall()]
        
        # Simple check for very similar names (case differences, extra spaces)
        potential_dupes = []
        seen = {}
        for author in authors:
            normalized = author.lower().strip()
            if normalized in seen:
                potential_dupes.append((seen[normalized], author))
            else:
                seen[normalized] = author
        
        if potential_dupes:
            self.log_issue(
                'Duplicate Authors',
                'WARNING',
                f'Found {len(potential_dupes)} potential duplicate author names',
                [f"'{d[0]}' vs '{d[1]}'" for d in potential_dupes[:10]]
            )
        return len(potential_dupes)
    
    # ============================================================================
    # TEST 4: Check Data Consistency
    # ============================================================================
    def test_orphaned_authors(self):
        """Check for authors not linked to any books"""
        self.cursor.execute('''
            SELECT a.id, a.author_name 
            FROM authors a
            LEFT JOIN book_authors ba ON a.id = ba.author_id
            WHERE ba.author_id IS NULL
        ''')
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Orphaned Authors',
                'WARNING',
                f'Found {len(results)} authors not linked to any books',
                [f"Author ID {r[0]}: {r[1]}" for r in results[:10]]
            )
        return len(results)
    
    def test_orphaned_subjects(self):
        """Check for subjects not linked to any books"""
        self.cursor.execute('''
            SELECT s.id, s.subject_name 
            FROM subjects s
            LEFT JOIN book_subjects bs ON s.id = bs.subject_id
            WHERE bs.subject_id IS NULL
        ''')
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Orphaned Subjects',
                'WARNING',
                f'Found {len(results)} subjects not linked to any books',
                [f"Subject ID {r[0]}: {r[1]}" for r in results[:10]]
            )
        return len(results)
    
    def test_orphaned_series(self):
        """Check for series not linked to any books"""
        self.cursor.execute('''
            SELECT s.id, s.series_name 
            FROM series s
            LEFT JOIN book_series bs ON s.id = bs.series_id
            WHERE bs.series_id IS NULL
        ''')
        results = self.cursor.fetchall()
        
        if results:
            self.log_issue(
                'Orphaned Series',
                'WARNING',
                f'Found {len(results)} series not linked to any books',
                [f"Series ID {r[0]}: {r[1]}" for r in results[:10]]
            )
        return len(results)
    
    def test_series_gaps(self):
        """Check for gaps in series numbering"""
        self.cursor.execute('''
            SELECT s.series_name, GROUP_CONCAT(bs.series_index) as indices, COUNT(*) as book_count
            FROM series s
            JOIN book_series bs ON s.id = bs.series_id
            GROUP BY s.series_name
            HAVING book_count > 1
        ''')
        results = self.cursor.fetchall()
        
        gaps_found = []
        for series_name, indices_str, count in results:
            if indices_str:
                indices = sorted([float(i) for i in indices_str.split(',') if i])
                # Check for gaps
                for i in range(len(indices) - 1):
                    if indices[i+1] - indices[i] > 1:
                        gaps_found.append(f"{series_name}: Gap between #{indices[i]} and #{indices[i+1]}")
        
        if gaps_found:
            self.log_issue(
                'Series Gaps',
                'INFO',
                f'Found {len(gaps_found)} series with gaps in numbering',
                gaps_found[:10]
            )
        return len(gaps_found)
    
    # ============================================================================
    # TEST 5: Data Statistics and Quality Metrics
    # ============================================================================
    def collect_statistics(self):
        """Collect overall database statistics"""
        # Total counts
        self.cursor.execute("SELECT COUNT(*) FROM books")
        self.stats['total_books'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM authors")
        self.stats['total_authors'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM series")
        self.stats['total_series'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM subjects")
        self.stats['total_subjects'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM book_files")
        self.stats['total_files'] = self.cursor.fetchone()[0]
        
        # Books with metadata
        self.cursor.execute("SELECT COUNT(*) FROM books WHERE metadata_path IS NOT NULL")
        self.stats['books_with_opf'] = self.cursor.fetchone()[0]
        
        # Books with covers
        self.cursor.execute("SELECT COUNT(*) FROM books WHERE cover_path IS NOT NULL")
        self.stats['books_with_covers'] = self.cursor.fetchone()[0]
        
        # Books in series
        self.cursor.execute("SELECT COUNT(DISTINCT book_id) FROM book_series")
        self.stats['books_in_series'] = self.cursor.fetchone()[0]
        
        # File format breakdown
        self.cursor.execute("SELECT file_format, COUNT(*) FROM book_files GROUP BY file_format")
        self.stats['file_formats'] = dict(self.cursor.fetchall())
        
        # Average books per author
        if self.stats['total_authors'] > 0:
            self.stats['avg_books_per_author'] = round(self.stats['total_books'] / self.stats['total_authors'], 2)
        
        # Authors with most books
        self.cursor.execute('''
            SELECT a.author_name, COUNT(*) as book_count
            FROM authors a
            JOIN book_authors ba ON a.id = ba.author_id
            GROUP BY a.author_name
            ORDER BY book_count DESC
            LIMIT 10
        ''')
        self.stats['top_authors'] = self.cursor.fetchall()
        
        # Largest series
        self.cursor.execute('''
            SELECT s.series_name, COUNT(*) as book_count
            FROM series s
            JOIN book_series bs ON s.id = bs.series_id
            GROUP BY s.series_name
            ORDER BY book_count DESC
            LIMIT 10
        ''')
        self.stats['largest_series'] = self.cursor.fetchall()
    
    # ============================================================================
    # Main Test Runner
    # ============================================================================
    def run_all_tests(self):
        """Run all data quality tests"""
        if not self.connect():
            return
        
        self.print_separator("DATA QUALITY TESTS - STARTING")
        
        print("\n🔍 Running completeness tests...")
        missing_titles = self.test_missing_titles()
        missing_authors = self.test_missing_authors()
        missing_files = self.test_missing_files()
        
        print("\n🔍 Running file integrity tests...")
        missing_folders = self.test_missing_book_folders()
        missing_covers = self.test_missing_cover_files()
        missing_ebooks = self.test_missing_ebook_files()
        
        print("\n🔍 Running duplicate detection tests...")
        duplicate_books = self.test_duplicate_books()
        duplicate_authors = self.test_duplicate_authors()
        
        print("\n🔍 Running consistency tests...")
        orphaned_authors = self.test_orphaned_authors()
        orphaned_subjects = self.test_orphaned_subjects()
        orphaned_series = self.test_orphaned_series()
        series_gaps = self.test_series_gaps()
        
        print("\n📊 Collecting statistics...")
        self.collect_statistics()
        
        # Print results
        self.print_results()
        
        self.conn.close()
    
    def print_results(self):
        """Print test results summary"""
        self.print_separator("DATA QUALITY TEST RESULTS")
        
        # Print statistics
        print("\n📊 DATABASE STATISTICS:")
        print(f"  Total Books: {self.stats['total_books']}")
        print(f"  Total Authors: {self.stats['total_authors']}")
        print(f"  Total Series: {self.stats['total_series']}")
        print(f"  Total Subjects: {self.stats['total_subjects']}")
        print(f"  Total Files: {self.stats['total_files']}")
        print(f"  Books with OPF metadata: {self.stats['books_with_opf']} ({self.stats['books_with_opf']/self.stats['total_books']*100:.1f}%)")
        print(f"  Books with covers: {self.stats['books_with_covers']} ({self.stats['books_with_covers']/self.stats['total_books']*100:.1f}%)")
        print(f"  Books in series: {self.stats['books_in_series']} ({self.stats['books_in_series']/self.stats['total_books']*100:.1f}%)")
        
        if self.stats.get('avg_books_per_author'):
            print(f"  Average books per author: {self.stats['avg_books_per_author']}")
        
        print("\n  File Formats:")
        for fmt, count in self.stats['file_formats'].items():
            print(f"    {fmt}: {count}")
        
        print("\n  Top 10 Authors by Book Count:")
        for author, count in self.stats['top_authors']:
            print(f"    {author}: {count} books")
        
        if self.stats['largest_series']:
            print("\n  Top 10 Largest Series:")
            for series, count in self.stats['largest_series']:
                print(f"    {series}: {count} books")
        
        # Print errors
        if self.issues:
            self.print_separator(f"❌ ERRORS FOUND: {len(self.issues)}")
            for issue in self.issues:
                print(f"\n❌ {issue['test']}: {issue['message']}")
                if issue['details']:
                    print("  Examples:")
                    for detail in issue['details'][:5]:
                        print(f"    - {detail}")
                    if len(issue['details']) > 5:
                        print(f"    ... and {len(issue['details']) - 5} more")
        else:
            print("\n✅ No critical errors found!")
        
        # Print warnings
        if self.warnings:
            self.print_separator(f"⚠️  WARNINGS FOUND: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"\n⚠️  {warning['test']}: {warning['message']}")
                if warning['details']:
                    print("  Examples:")
                    for detail in warning['details'][:5]:
                        print(f"    - {detail}")
                    if len(warning['details']) > 5:
                        print(f"    ... and {len(warning['details']) - 5} more")
        else:
            print("\n✅ No warnings!")
        
        # Overall quality score
        total_tests = 12
        failed_tests = len(self.issues)
        warning_tests = len(self.warnings)
        passed_tests = total_tests - failed_tests - warning_tests
        
        quality_score = (passed_tests / total_tests) * 100
        
        self.print_separator("OVERALL DATA QUALITY SCORE")
        print(f"\n  Passed: {passed_tests}/{total_tests}")
        print(f"  Warnings: {warning_tests}/{total_tests}")
        print(f"  Failed: {failed_tests}/{total_tests}")
        print(f"\n  Quality Score: {quality_score:.1f}%")
        
        if quality_score >= 90:
            print("  Rating: ⭐⭐⭐⭐⭐ Excellent")
        elif quality_score >= 75:
            print("  Rating: ⭐⭐⭐⭐ Good")
        elif quality_score >= 60:
            print("  Rating: ⭐⭐⭐ Fair")
        else:
            print("  Rating: ⭐⭐ Needs Improvement")
        
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    checker = DataQualityChecker()
    checker.run_all_tests()