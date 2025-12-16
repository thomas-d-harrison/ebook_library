import os
import shutil
from pathlib import Path
from difflib import SequenceMatcher

class EbookFolderCleaner:
    def __init__(self, library_path):
        self.library_path = Path(library_path)
        self.ebook_extensions = {'.epub', '.mobi', '.azw', '.azw3', '.pdf', '.txt', '.fb2', '.djvu', '.cbr'}
        self.empty_folders = []
        self.duplicate_candidates = []
    
    def has_ebook_files(self, folder_path):
        """Check if a folder contains any ebook files"""
        for file in folder_path.iterdir():
            if file.is_file() and file.suffix.lower() in self.ebook_extensions:
                return True
        return False
    
    def get_folder_info(self, folder_path):
        """Get information about files in a folder"""
        files = list(folder_path.iterdir())
        ebook_count = sum(1 for f in files if f.is_file() and f.suffix.lower() in self.ebook_extensions)
        metadata_count = sum(1 for f in files if f.suffix.lower() == '.opf')
        cover_count = sum(1 for f in files if f.suffix.lower() in ['.jpg', '.jpeg', '.png'])
        
        return {
            'path': folder_path,
            'name': folder_path.name,
            'ebook_count': ebook_count,
            'metadata_count': metadata_count,
            'cover_count': cover_count,
            'total_files': len(files)
        }
    
    def similarity_ratio(self, str1, str2):
        """Calculate similarity between two strings (0-1)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def scan_for_empty_folders(self):
        """Scan library and find folders without ebook files"""
        print("Scanning library for empty book folders...")
        print("="*60)
        
        author_count = 0
        
        # Walk through Author folders
        for author_folder in self.library_path.iterdir():
            if not author_folder.is_dir():
                continue
            
            author_count += 1
            author_name = author_folder.name
            book_folders = []
            
            # Collect all book folders for this author
            for book_folder in author_folder.iterdir():
                if not book_folder.is_dir():
                    continue
                
                info = self.get_folder_info(book_folder)
                book_folders.append(info)
                
                # Track empty folders
                if info['ebook_count'] == 0:
                    self.empty_folders.append(info)
            
            # Find potential duplicates within the same author
            if len(book_folders) > 1:
                self.find_duplicates_in_author(author_name, book_folders)
        
        print(f"\nScanned {author_count} authors")
        print(f"Found {len(self.empty_folders)} folders without ebook files")
        print(f"Found {len(self.duplicate_candidates)} potential duplicate groups")
    
    def find_duplicates_in_author(self, author_name, book_folders):
        """Find similar book folders under the same author"""
        # Compare each pair of folders
        for i, folder1 in enumerate(book_folders):
            for folder2 in book_folders[i+1:]:
                similarity = self.similarity_ratio(folder1['name'], folder2['name'])
                
                # If names are very similar (>70% match)
                if similarity > 0.7:
                    # One has ebooks, one doesn't
                    if folder1['ebook_count'] > 0 and folder2['ebook_count'] == 0:
                        self.duplicate_candidates.append({
                            'author': author_name,
                            'keep': folder1,
                            'remove': folder2,
                            'similarity': similarity
                        })
                    elif folder2['ebook_count'] > 0 and folder1['ebook_count'] == 0:
                        self.duplicate_candidates.append({
                            'author': author_name,
                            'keep': folder2,
                            'remove': folder1,
                            'similarity': similarity
                        })
    
    def display_empty_folders(self):
        """Display all folders without ebook files"""
        if not self.empty_folders:
            print("\n✓ No empty folders found!")
            return
        
        print("\n" + "="*60)
        print("FOLDERS WITHOUT EBOOK FILES:")
        print("="*60)
        
        for i, folder in enumerate(self.empty_folders, 1):
            print(f"\n{i}. {folder['name']}")
            print(f"   Path: {folder['path']}")
            print(f"   Contains: {folder['metadata_count']} metadata, {folder['cover_count']} covers, {folder['total_files']} total files")
    
    def display_duplicate_candidates(self):
        """Display potential duplicate folders"""
        if not self.duplicate_candidates:
            print("\n✓ No duplicate candidates found!")
            return
        
        print("\n" + "="*60)
        print("POTENTIAL DUPLICATE FOLDERS:")
        print("="*60)
        
        for i, dup in enumerate(self.duplicate_candidates, 1):
            print(f"\n{i}. Author: {dup['author']}")
            print(f"   Similarity: {dup['similarity']*100:.1f}%")
            print(f"   KEEP:   {dup['keep']['name']} ({dup['keep']['ebook_count']} ebooks)")
            print(f"   DELETE: {dup['remove']['name']} ({dup['remove']['ebook_count']} ebooks)")
    
    def delete_empty_folders(self, confirm=True):
        """Delete all folders without ebook files"""
        if not self.empty_folders:
            print("\nNo empty folders to delete.")
            return
        
        if confirm:
            print(f"\n⚠️  WARNING: About to delete {len(self.empty_folders)} folders!")
            response = input("Are you sure you want to delete all empty folders? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Deletion cancelled.")
                return
        
        deleted_count = 0
        failed_count = 0
        
        for folder in self.empty_folders:
            try:
                shutil.rmtree(folder['path'])
                print(f"✓ Deleted: {folder['name']}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {folder['name']}: {e}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"Deleted {deleted_count} folders")
        if failed_count > 0:
            print(f"Failed to delete {failed_count} folders")
    
    def delete_duplicate_folders(self, confirm=True):
        """Delete duplicate folders (ones without ebook files)"""
        if not self.duplicate_candidates:
            print("\nNo duplicate folders to delete.")
            return
        
        if confirm:
            print(f"\n⚠️  WARNING: About to delete {len(self.duplicate_candidates)} duplicate folders!")
            response = input("Are you sure you want to delete duplicate folders? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Deletion cancelled.")
                return
        
        deleted_count = 0
        failed_count = 0
        
        for dup in self.duplicate_candidates:
            try:
                shutil.rmtree(dup['remove']['path'])
                print(f"✓ Deleted: {dup['remove']['name']} (kept {dup['keep']['name']})")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {dup['remove']['name']}: {e}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"Deleted {deleted_count} duplicate folders")
        if failed_count > 0:
            print(f"Failed to delete {failed_count} folders")
    
    def export_report(self, filename='cleanup_report.txt'):
        """Export a report of findings to a text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("EBOOK LIBRARY CLEANUP REPORT\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Empty Folders: {len(self.empty_folders)}\n")
            f.write(f"Duplicate Candidates: {len(self.duplicate_candidates)}\n\n")
            
            f.write("="*60 + "\n")
            f.write("FOLDERS WITHOUT EBOOK FILES:\n")
            f.write("="*60 + "\n\n")
            
            for folder in self.empty_folders:
                f.write(f"{folder['name']}\n")
                f.write(f"  Path: {folder['path']}\n\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("POTENTIAL DUPLICATES:\n")
            f.write("="*60 + "\n\n")
            
            for dup in self.duplicate_candidates:
                f.write(f"Author: {dup['author']}\n")
                f.write(f"  Similarity: {dup['similarity']*100:.1f}%\n")
                f.write(f"  KEEP:   {dup['keep']['name']}\n")
                f.write(f"  DELETE: {dup['remove']['name']}\n\n")
        
        print(f"\n✓ Report exported to: {filename}")

def main():
    print("="*60)
    print("EBOOK LIBRARY FOLDER CLEANUP TOOL")
    print("="*60)
    print("\nThis tool will:")
    print("1. Find folders without any ebook files")
    print("2. Identify potential duplicate folders")
    print("3. Allow you to safely delete empty/duplicate folders")
    print("\n" + "="*60)
    
    # Get library path
    library_path = input("\nEnter the path to your ebook library folder: ").strip()
    library_path = library_path.strip('"').strip("'")
    
    if not os.path.exists(library_path):
        print(f"Error: Path does not exist: {library_path}")
        return
    
    # Create cleaner instance and scan
    cleaner = EbookFolderCleaner(library_path)
    cleaner.scan_for_empty_folders()
    
    # Display findings
    cleaner.display_empty_folders()
    cleaner.display_duplicate_candidates()
    
    # Export report
    print("\n" + "="*60)
    export = input("\nExport report to file? (yes/no): ").strip().lower()
    if export == 'yes':
        cleaner.export_report()
    
    # Menu for actions
    while True:
        print("\n" + "="*60)
        print("CLEANUP OPTIONS:")
        print("="*60)
        print("1. Delete ALL empty folders (folders without ebook files)")
        print("2. Delete only DUPLICATE folders (similar names, no ebooks)")
        print("3. Export report again")
        print("4. Exit (no deletion)")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            cleaner.delete_empty_folders(confirm=True)
            break
        elif choice == '2':
            cleaner.delete_duplicate_folders(confirm=True)
            break
        elif choice == '3':
            cleaner.export_report()
        elif choice == '4':
            print("\nExiting without deleting any folders.")
            break
        else:
            print("Invalid choice. Please enter 1-4.")
    
    print("\n" + "="*60)
    print("Cleanup complete!")
    print("="*60)

if __name__ == "__main__":
    main()