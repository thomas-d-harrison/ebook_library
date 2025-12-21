import sqlite3
import re
from collections import Counter

class SubjectCleanup:
    def __init__(self, db_path='../infra/data/tt_db_ebook_lib.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Common subject mappings for standardization
        # These map variations to a standard form, but preserve distinct categories
        self.subject_mappings = {
            # Science Fiction variations
            'sci-fi': 'Science Fiction',
            'scifi': 'Science Fiction',
            'sf': 'Science Fiction',
            'fiction / science fiction': 'Science Fiction',
            'fiction - science fiction': 'Science Fiction',
            'sci fi': 'Science Fiction',
            
            # Fantasy variations
            'fantasy fiction': 'Fantasy',
            'fiction / fantasy': 'Fantasy',
            'fiction - fantasy': 'Fantasy',
            
            # Mystery variations
            'mystery & detective': 'Mystery',
            'detective fiction': 'Mystery',
            'detective and mystery': 'Mystery',
            'fiction / mystery & detective': 'Mystery',
            
            # Thriller variations
            'suspense': 'Thriller',
            'thrillers': 'Thriller',
            
            # Romance variations
            'romance fiction': 'Romance',
            'fiction / romance': 'Romance',
            
            # Young Adult variations
            'juvenile fiction': 'Young Adult',
            'young adult fiction': 'Young Adult',
            'ya': 'Young Adult',
            'ya fiction': 'Young Adult',
            
            # Historical variations
            'historical fiction': 'Historical Fiction',
            'fiction / historical': 'Historical Fiction',
            
            # Biography variations
            'biography & autobiography': 'Biography',
            'autobiography': 'Biography',
            'biographies': 'Biography',
            
            # Nonfiction variations
            'non-fiction': 'Nonfiction',
            'non fiction': 'Nonfiction',
            
            # Self Help variations
            'self-help': 'Self Help',
            'selfhelp': 'Self Help',
            'self improvement': 'Self Help',
            'self-improvement': 'Self Help',
            
            # Horror variations
            'horror fiction': 'Horror',
            'fiction / horror': 'Horror',
            
            # Adventure variations
            'adventure fiction': 'Adventure',
            'fiction / adventure': 'Adventure',
            
            # Literary Fiction variations
            'literary fiction': 'Literary Fiction',
            'fiction / literary': 'Literary Fiction',
            'literature': 'Literary Fiction',
            
            # Business variations
            'business & economics': 'Business',
            'economics': 'Business',
            
            # Science variations
            'popular science': 'Science',
            'science & nature': 'Science',
            
            # History variations
            'history / general': 'History',
            
            # Philosophy variations
            'philosophy / general': 'Philosophy',
            
            # Psychology variations
            'psychology / general': 'Psychology',
            
            # Religion variations
            'religion / general': 'Religion',
            'religious': 'Religion',
            
            # True Crime variations
            'true crime': 'True Crime',
            'crime': 'True Crime',
            
            # Poetry variations
            'poetry / general': 'Poetry',
            
            # Drama variations
            'drama / general': 'Drama',
            'plays': 'Drama',
            
            # Humor variations
            'humor / general': 'Humor',
            'humour': 'Humor',
            'comedy': 'Humor',
            
            # Travel variations
            'travel / general': 'Travel',
            
            # Cooking variations
            'cooking / general': 'Cooking',
            'cookbooks': 'Cooking',
            'food & wine': 'Cooking',
            
            # Art variations
            'art / general': 'Art',
            
            # Music variations
            'music / general': 'Music',
            
            # Sports variations
            'sports & recreation': 'Sports',
            'sports / general': 'Sports',
            
            # Nature variations
            'nature': 'Nature',
            'natural history': 'Nature',
            
            # Politics variations
            'political science': 'Politics',
            'politics / general': 'Politics',
            
            # Technology variations
            'computers': 'Technology',
            'computers / general': 'Technology',
            'technology & engineering': 'Technology',
            
            # Education variations
            'education / general': 'Education',
            
            # Parenting variations
            'family & relationships': 'Parenting',
            'parenting': 'Parenting',
            
            # Health variations
            'health & fitness': 'Health',
            'medical': 'Health',
            
            # Crafts variations
            'crafts & hobbies': 'Crafts',
            'hobbies': 'Crafts',
        }
        
        # Separators to split on (DO split compound subjects)
        self.separators = ['/', '|', ';', ' & ', ' and ']
    
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to database: {self.db_path}\n")
    
    def print_separator(self, title):
        """Print a formatted separator"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    
    def analyze_subjects(self):
        """Analyze current subjects and identify issues"""
        self.cursor.execute("SELECT id, subject_name FROM subjects ORDER BY subject_name")
        subjects = self.cursor.fetchall()
        
        issues = {
            'with_slashes': [],
            'with_pipes': [],
            'with_ampersands': [],
            'with_semicolons': [],
            'with_numbers': [],
            'with_special_chars': [],
            'very_long': [],
            'multiple_words_caps': [],
            'all_caps': [],
            'redundant_fiction': []
        }
        
        for subject_id, subject_name in subjects:
            # Check for various separators
            if '/' in subject_name:
                issues['with_slashes'].append((subject_id, subject_name))
            if '|' in subject_name:
                issues['with_pipes'].append((subject_id, subject_name))
            if '&' in subject_name:
                issues['with_ampersands'].append((subject_id, subject_name))
            if ';' in subject_name:
                issues['with_semicolons'].append((subject_id, subject_name))
            
            # Check for numbers
            if re.search(r'\d', subject_name):
                issues['with_numbers'].append((subject_id, subject_name))
            
            # Check for special characters (not letters, spaces, hyphens, apostrophes)
            if re.search(r'[^a-zA-Z0-9\s\-\']', subject_name):
                issues['with_special_chars'].append((subject_id, subject_name))
            
            # Check for very long subjects
            if len(subject_name) > 50:
                issues['very_long'].append((subject_id, subject_name))
            
            # Check for ALL CAPS
            if subject_name.isupper() and len(subject_name) > 3:
                issues['all_caps'].append((subject_id, subject_name))
            
            # Check for redundant "Fiction" (e.g., "Fiction - Science Fiction")
            if subject_name.lower().startswith('fiction -') or subject_name.lower().startswith('fiction /'):
                issues['redundant_fiction'].append((subject_id, subject_name))
        
        return issues
    
    def print_analysis(self, issues):
        """Print analysis results"""
        self.print_separator("SUBJECT ANALYSIS REPORT")
        
        print(f"\n📊 Issues Found:")
        print(f"  Subjects with slashes (/): {len(issues['with_slashes'])}")
        print(f"  Subjects with pipes (|): {len(issues['with_pipes'])}")
        print(f"  Subjects with ampersands (&): {len(issues['with_ampersands'])}")
        print(f"  Subjects with semicolons (;): {len(issues['with_semicolons'])}")
        print(f"  Subjects with numbers: {len(issues['with_numbers'])}")
        print(f"  Subjects with special characters: {len(issues['with_special_chars'])}")
        print(f"  Very long subjects (>50 chars): {len(issues['very_long'])}")
        print(f"  ALL CAPS subjects: {len(issues['all_caps'])}")
        print(f"  Redundant 'Fiction' prefix: {len(issues['redundant_fiction'])}")
        
        # Show examples
        if issues['with_slashes']:
            print(f"\n  Examples of subjects with slashes:")
            for subject_id, subject_name in issues['with_slashes'][:10]:
                print(f"    - {subject_name}")
        
        if issues['with_ampersands']:
            print(f"\n  Examples of subjects with ampersands:")
            for subject_id, subject_name in issues['with_ampersands'][:10]:
                print(f"    - {subject_name}")
        
        if issues['very_long']:
            print(f"\n  Examples of very long subjects:")
            for subject_id, subject_name in issues['very_long'][:5]:
                print(f"    - {subject_name}")
        
        if issues['all_caps']:
            print(f"\n  Examples of ALL CAPS subjects:")
            for subject_id, subject_name in issues['all_caps'][:10]:
                print(f"    - {subject_name}")
    
    def normalize_subject(self, subject_name):
        """Normalize a subject name"""
        # Trim whitespace
        subject = subject_name.strip()
        
        # Remove "Fiction - " or "Fiction / " prefix
        subject = re.sub(r'^Fiction\s*[-/]\s*', '', subject, flags=re.IGNORECASE)
        
        # Convert to title case if ALL CAPS
        if subject.isupper():
            subject = subject.title()
        
        # Check against mappings
        subject_lower = subject.lower()
        if subject_lower in self.subject_mappings:
            return self.subject_mappings[subject_lower]
        
        return subject
    
    def split_subject(self, subject_name):
        """Split a subject that contains multiple subjects"""
        subjects = [subject_name]
        
        # Try each separator
        for separator in self.separators:
            new_subjects = []
            for subj in subjects:
                if separator in subj:
                    parts = [p.strip() for p in subj.split(separator) if p.strip()]
                    new_subjects.extend(parts)
                else:
                    new_subjects.append(subj)
            subjects = new_subjects
        
        # Normalize each split subject
        normalized = [self.normalize_subject(s) for s in subjects]
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for s in normalized:
            if s.lower() not in seen:
                seen.add(s.lower())
                result.append(s)
        
        return result
    
    def find_duplicates(self):
        """Find duplicate subjects (case-insensitive)"""
        self.cursor.execute("SELECT id, subject_name FROM subjects")
        subjects = self.cursor.fetchall()
        
        # Group by lowercase name
        grouped = {}
        for subject_id, subject_name in subjects:
            key = subject_name.lower().strip()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append((subject_id, subject_name))
        
        # Find duplicates
        duplicates = {k: v for k, v in grouped.items() if len(v) > 1}
        
        if duplicates:
            self.print_separator("DUPLICATE SUBJECTS FOUND")
            for key, items in duplicates.items():
                print(f"\n  '{key}' has {len(items)} variations:")
                for subject_id, subject_name in items:
                    # Count how many books use this subject
                    self.cursor.execute("SELECT COUNT(*) FROM book_subjects WHERE subject_id = ?", (subject_id,))
                    book_count = self.cursor.fetchone()[0]
                    print(f"    - ID {subject_id}: '{subject_name}' ({book_count} books)")
        
        return duplicates
    
    def clean_subjects(self, dry_run=True):
        """Clean and standardize subjects"""
        self.print_separator("CLEANING SUBJECTS")
        
        if dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made\n")
        
        self.cursor.execute("SELECT id, subject_name FROM subjects")
        subjects = self.cursor.fetchall()
        
        changes_made = 0
        subjects_added = 0
        
        for subject_id, subject_name in subjects:
            # Get books using this subject
            self.cursor.execute("SELECT book_id FROM book_subjects WHERE subject_id = ?", (subject_id,))
            book_ids = [row[0] for row in self.cursor.fetchall()]
            
            # Split and normalize
            new_subjects = self.split_subject(subject_name)
            
            # If we got multiple subjects from splitting
            if len(new_subjects) > 1:
                print(f"\n  Splitting: '{subject_name}'")
                print(f"    → Into: {new_subjects}")
                
                if not dry_run:
                    # Add each new subject and link to books
                    for new_subject in new_subjects:
                        # Get or create subject
                        self.cursor.execute("SELECT id FROM subjects WHERE subject_name = ?", (new_subject,))
                        result = self.cursor.fetchone()
                        
                        if result:
                            new_subject_id = result[0]
                        else:
                            self.cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (new_subject,))
                            new_subject_id = self.cursor.lastrowid
                            subjects_added += 1
                        
                        # Link to all books that had the original subject
                        for book_id in book_ids:
                            self.cursor.execute(
                                "INSERT OR IGNORE INTO book_subjects (book_id, subject_id) VALUES (?, ?)",
                                (book_id, new_subject_id)
                            )
                    
                    # Remove old subject links
                    self.cursor.execute("DELETE FROM book_subjects WHERE subject_id = ?", (subject_id,))
                    
                    # Delete old subject if no longer used
                    self.cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
                
                changes_made += 1
            
            # If just normalizing (no split)
            elif new_subjects[0] != subject_name:
                print(f"\n  Normalizing: '{subject_name}'")
                print(f"    → To: '{new_subjects[0]}'")
                
                if not dry_run:
                    # Check if normalized subject already exists
                    self.cursor.execute("SELECT id FROM subjects WHERE subject_name = ?", (new_subjects[0],))
                    result = self.cursor.fetchone()
                    
                    if result:
                        # Merge into existing subject
                        new_subject_id = result[0]
                        for book_id in book_ids:
                            self.cursor.execute(
                                "INSERT OR IGNORE INTO book_subjects (book_id, subject_id) VALUES (?, ?)",
                                (book_id, new_subject_id)
                            )
                        self.cursor.execute("DELETE FROM book_subjects WHERE subject_id = ?", (subject_id,))
                        self.cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
                    else:
                        # Just rename
                        self.cursor.execute(
                            "UPDATE subjects SET subject_name = ? WHERE id = ?",
                            (new_subjects[0], subject_id)
                        )
                
                changes_made += 1
        
        if not dry_run:
            self.conn.commit()
            print(f"\n✓ Changes committed to database")
        
        print(f"\n📊 Summary:")
        print(f"  Subjects modified: {changes_made}")
        print(f"  New subjects created: {subjects_added}")
        
        if dry_run:
            print(f"\n  Run with dry_run=False to apply these changes")
    
    def interactive_cleanup(self):
        """Interactive cleanup session"""
        self.connect()
        
        while True:
            self.print_separator("SUBJECT CLEANUP MENU")
            print("\n1. Analyze subjects (show issues)")
            print("2. Find duplicate subjects")
            print("3. Preview cleanup (dry run)")
            print("4. Apply cleanup (make changes)")
            print("5. Show all subjects")
            print("6. Search subjects")
            print("7. Manually merge subjects")
            print("8. Quit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                issues = self.analyze_subjects()
                self.print_analysis(issues)
            
            elif choice == '2':
                self.find_duplicates()
            
            elif choice == '3':
                self.clean_subjects(dry_run=True)
            
            elif choice == '4':
                confirm = input("\n⚠️  This will modify your database. Are you sure? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    self.clean_subjects(dry_run=False)
                else:
                    print("Cancelled.")
            
            elif choice == '5':
                self.cursor.execute('''
                    SELECT s.subject_name, COUNT(bs.book_id) as book_count
                    FROM subjects s
                    LEFT JOIN book_subjects bs ON s.id = bs.subject_id
                    GROUP BY s.subject_name
                    ORDER BY book_count DESC, s.subject_name
                ''')
                results = self.cursor.fetchall()
                print(f"\nTotal subjects: {len(results)}")
                for subject_name, book_count in results[:50]:
                    print(f"  {subject_name}: {book_count} books")
                if len(results) > 50:
                    print(f"  ... and {len(results) - 50} more")
            
            elif choice == '6':
                search = input("\nEnter search term: ").strip()
                self.cursor.execute('''
                    SELECT s.id, s.subject_name, COUNT(bs.book_id) as book_count
                    FROM subjects s
                    LEFT JOIN book_subjects bs ON s.id = bs.subject_id
                    WHERE s.subject_name LIKE ?
                    GROUP BY s.id, s.subject_name
                ''', (f'%{search}%',))
                results = self.cursor.fetchall()
                if results:
                    print(f"\nFound {len(results)} subjects:")
                    for subject_id, subject_name, book_count in results:
                        print(f"  ID {subject_id}: {subject_name} ({book_count} books)")
                else:
                    print("No subjects found.")
            
            elif choice == '7':
                print("\n--- Manual Subject Merge ---")
                from_id = input("Enter ID of subject to merge FROM: ").strip()
                to_id = input("Enter ID of subject to merge INTO: ").strip()
                
                try:
                    from_id = int(from_id)
                    to_id = int(to_id)
                    
                    # Get subject names
                    self.cursor.execute("SELECT subject_name FROM subjects WHERE id = ?", (from_id,))
                    from_name = self.cursor.fetchone()
                    self.cursor.execute("SELECT subject_name FROM subjects WHERE id = ?", (to_id,))
                    to_name = self.cursor.fetchone()
                    
                    if not from_name or not to_name:
                        print("❌ One or both subject IDs not found")
                        continue
                    
                    print(f"\nMerge '{from_name[0]}' → '{to_name[0]}'")
                    confirm = input("Confirm? (yes/no): ").strip().lower()
                    
                    if confirm == 'yes':
                        # Update all book_subjects to point to the target subject
                        self.cursor.execute(
                            "UPDATE OR IGNORE book_subjects SET subject_id = ? WHERE subject_id = ?",
                            (to_id, from_id)
                        )
                        # Delete old links
                        self.cursor.execute("DELETE FROM book_subjects WHERE subject_id = ?", (from_id,))
                        # Delete old subject
                        self.cursor.execute("DELETE FROM subjects WHERE id = ?", (from_id,))
                        self.conn.commit()
                        print("✓ Subjects merged successfully")
                    else:
                        print("Cancelled.")
                except ValueError:
                    print("❌ Invalid ID")
            
            elif choice == '8':
                break
            
            else:
                print("Invalid choice.")
        
        self.conn.close()
        print("\nDone!")

if __name__ == "__main__":
    cleanup = SubjectCleanup()
    cleanup.interactive_cleanup()