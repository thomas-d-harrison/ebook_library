import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Publisher standardization mappings
PUBLISHER_MAP = {
    # HarperCollins variations
    'Harper Collins': 'HarperCollins',
    'Harper Collins Audio': 'HarperCollins',
    'HarperCollinsPublishers': 'HarperCollins',
    'HarperCollins Publishers': 'HarperCollins',
    'HarperCollins Publishers Australia': 'HarperCollins',
    'HarperCollins Publishers Limited': 'HarperCollins',
    'HarperCollins UK': 'HarperCollins',
    'Harpercollins Audio': 'HarperCollins',
    'Harpercollins Pb': 'HarperCollins',
    'HarperPaperbacks': 'HarperCollins',
    'Harper Paperbacks': 'HarperCollins',
    'Harper': 'HarperCollins',
    'HarperVoyager': 'HarperCollins',
    'Harper Voyager': 'HarperCollins',
    
    # Penguin variations
    'Penguin Books Limited': 'Penguin Random House',
    'Penguin Canada': 'Penguin Random House',
    'Penguin Group': 'Penguin Random House',
    'Penguin Group USA, Inc.': 'Penguin Random House',
    'Penguin Group USA, Incorporated': 'Penguin Random House',
    'Penguin Publishing Group': 'Penguin Random House',
    'Penguin UK': 'Penguin Random House',
    'Penguin Random House Australia': 'Penguin Random House',
    'Penguin Random House LLC': 'Penguin Random House',
    'Penguin Random House South Africa': 'Penguin Random House',
    
    # Random House variations
    'Random House Publishing Group': 'Penguin Random House',
    'Random House Publishing Group - Del Rey Spectra': 'Penguin Random House',
    'Random House Value Publishing': 'Penguin Random House',
    'Random House Worlds': 'Penguin Random House',
    'Random House, Inc.': 'Penguin Random House',
    
    # Bloomsbury variations
    'Bloomsbury Circus': 'Bloomsbury Publishing',
    'Bloomsbury Publishing Plc': 'Bloomsbury Publishing',
    'Bloomsbury Publishing USA': 'Bloomsbury Publishing',
    'Bloomsbury USA': 'Bloomsbury Publishing',
    
    # Farrar, Straus variations
    'Farrar, Straus and Giroux': 'Farrar, Straus and Giroux',
    'Farrar, Straus, Giroux': 'Farrar, Straus and Giroux',
    'Farrar, Straus and Giroux (BYR)': 'Farrar, Straus and Giroux',
    
    # Oxford variations
    'OUP Oxford': 'Oxford University Press',
    'Oxford University Press, UK': 'Oxford University Press',
    
    # Little, Brown variations
    'Little, Brown': 'Little, Brown and Company',
    'Little, Brown Book Group': 'Little, Brown and Company',
    'Little, Brown Book Group Limited': 'Little, Brown and Company',
    
    # Macmillan variations
    'Macmillan + ORM': 'Macmillan',
    
    # Simon & Schuster variations
    'Simon and Schuster': 'Simon & Schuster',
    
    # Hachette variations
    'Hachette+ORM': 'Hachette Books',
    
    # Knopf variations
    'Knopf Canada': 'Alfred A. Knopf',
    'Knopf': 'Alfred A. Knopf',
    'Knopf Doubleday Publishing Group': 'Alfred A. Knopf',
    
    # Barnes & Noble variations
    'Barnes&Noble': 'Barnes & Noble',
    
    # W. W. Norton variations
    'Norton': 'W. W. Norton & Company',
    
    # Houghton Mifflin variations
    'Houghton Mifflin': 'Houghton Mifflin Harcourt',
    
    # Scholastic variations
    'Scholastic Inc.': 'Scholastic',
    
    # Vintage variations
    'Vintage Books': 'Vintage',
    
    # Faber variations
    'Faber & Faber, Limited': 'Faber & Faber',
    
    # Doubleday variations
    'Doubleday & Company, Incorporated': 'Doubleday Canada',
    
    # Grove variations
    'Grove/Atlantic, Inc.': 'Grove Press',
    
    # Europa variations
    'Europa Editions, Incorporated': 'Europa Editions',
    
    # Orion variations
    'Orion Publishing Group, Limited': 'Orion',
    
    # Pan Macmillan variations
    'Pan Books': 'Pan Macmillan',
    'Pan Macmillan India Publishing Private Limited': 'Pan Macmillan',
    'Pan Macmillan UK': 'Pan Macmillan',
    
    # Profile variations
    'Profile Books Limited': 'Profile Books',
    
    # Oldcastle variations
    'Oldcastle Books, Limited': 'Oldcastle Books',
    
    # Text Publishing variations
    'Text Publishing Company': 'Text Publishing',
    
    # Transworld variations
    'Transworld Publishers Limited': 'Transworld',
    
    # Turtleback variations
    'Turtleback Books Distributed by Demco Media': 'Turtleback',
    
    # Thorndike variations
    'Thorndike Press, a part of Gale, a Cengage Company': 'Thorndike Press',
    
    # Gale variations
    'Gale, a Cengage Company': 'Gale',
    
    # Shambhala variations
    'Shambhala Publications, Incorporated': 'Shambhala Publications',
    
    # Tantor variations
    'Tantor Media, Incorporated': 'Tantor Media',
    
    # Harlequin variations
    'Harlequin Enterprises ULC': 'Harlequin',
    
    # Marvel variations
    'Marvel Worldwide, Incorporated': 'Marvel',
    
    # Zed variations
    'Zed Books Ltd.': 'Zed Books',
    
    # Creative Media variations
    'Creative Media Partners, LLC': 'Creative Media Partners',
    
    # University presses
    'Univ of California Press': 'University of California Press',
}

def fix_opf_publisher(opf_path):
    """Fix publisher name in a single OPF file"""
    try:
        # Register namespaces to preserve them
        ET.register_namespace('', 'http://www.idpf.org/2007/opf')
        ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
        ET.register_namespace('opf', 'http://www.idpf.org/2007/opf')
        
        tree = ET.parse(opf_path)
        root = tree.getroot()
        
        ns = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf'
        }
        
        # Find publisher element
        pub_elem = root.find('.//dc:publisher', ns)
        if pub_elem is None:
            pub_elem = root.find('.//publisher')
        
        if pub_elem is not None and pub_elem.text:
            original = pub_elem.text.strip()
            
            # Check if it needs standardization
            if original in PUBLISHER_MAP:
                standardized = PUBLISHER_MAP[original]
                pub_elem.text = standardized
                
                # Write back to file
                tree.write(opf_path, encoding='utf-8', xml_declaration=True)
                return True, original, standardized
            else:
                # Return the original even if not changed
                return False, original, None
        
        return False, None, None
        
    except Exception as e:
        print(f"Error processing {opf_path}: {e}")
        return False, None, None

def scan_and_fix_publishers(library_path):
    """Scan library and fix all publisher names"""
    library_path = Path(library_path)
    
    if not library_path.exists():
        print(f"Error: Library path does not exist: {library_path}")
        return
    
    total_files = 0
    fixed_files = 0
    changes = {}
    
    print("Scanning library for OPF files...")
    
    for author_folder in library_path.iterdir():
        if not author_folder.is_dir():
            continue
        
        if author_folder.name.startswith('.'):
            continue
        
        for book_folder in author_folder.iterdir():
            if not book_folder.is_dir():
                continue
            
            # Find OPF file
            for file in book_folder.iterdir():
                if file.suffix.lower() == '.opf':
                    total_files += 1
                    print(f"Checking: {book_folder.name}")
                    was_fixed, original, standardized = fix_opf_publisher(file)
                    
                    if was_fixed:
                        fixed_files += 1
                        if original not in changes:
                            changes[original] = []
                        changes[original].append(str(file))
                        print(f"  ✓ Fixed: '{original}' → '{standardized}'")
                    else:
                        if original:
                            print(f"  - Publisher '{original}' not in mapping (no change needed)")
                        else:
                            print(f"  - No publisher found")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total OPF files scanned: {total_files}")
    print(f"  Files updated: {fixed_files}")
    print(f"  Files unchanged: {total_files - fixed_files}")
    
    if changes:
        print(f"\n{'='*60}")
        print("Changes made by publisher:")
        for original, files in sorted(changes.items()):
            print(f"\n'{original}' → '{PUBLISHER_MAP[original]}' ({len(files)} files)")

if __name__ == "__main__":
    library_path = input("Enter the path to your ebook library folder: ").strip()
    library_path = library_path.strip('"').strip("'")
    
    confirm = input(f"\nThis will modify OPF files in: {library_path}\nContinue? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        scan_and_fix_publishers(library_path)
        print("\nDone! You can now re-run ebook_processor.py to update your database.")
    else:
        print("Operation cancelled.")