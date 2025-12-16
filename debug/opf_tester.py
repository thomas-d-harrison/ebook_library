import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def test_opf_parsing(opf_path):
    """Test parsing an OPF file to see what series data we can extract"""
    
    print("="*60)
    print(f"TESTING OPF FILE: {opf_path}")
    print("="*60)
    
    try:
        tree = ET.parse(opf_path)
        root = tree.getroot()
        
        # Print the entire XML structure to see what we're working with
        print("\nFull XML structure:")
        print(ET.tostring(root, encoding='unicode')[:1000])
        print("...\n")
        
        # Handle namespaces
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        print("\nLooking for series metadata...")
        print("-"*60)
        
        # Method 1: Look for calibre:series meta tag (without namespace)
        print("\n1. Searching for: .//meta[@name='calibre:series']")
        series_elem = root.find(".//meta[@name='calibre:series']")
        if series_elem is not None:
            print(f"   ✓ FOUND: {series_elem.get('content')}")
        else:
            print("   ✗ Not found")
        
        # Method 2: Look with namespace
        print("\n2. Searching for: .//opf:meta[@name='calibre:series']")
        series_elem2 = root.find(".//opf:meta[@name='calibre:series']", ns)
        if series_elem2 is not None:
            series_name = series_elem2.get('content')
            print(f"   ✓ FOUND: {series_name}")
            
            # Now test the series_index too
            print("\n   Also checking series_index...")
            series_index_elem = root.find(".//opf:meta[@name='calibre:series_index']", ns)
            if series_index_elem is not None:
                series_index = series_index_elem.get('content')
                print(f"   ✓ FOUND INDEX: {series_index}")
            else:
                print("   ✗ Index not found")
        else:
            print("   ✗ Not found")
        
        # Method 2b: Try with different namespace approach
        print("\n2b. Trying to find with {http://www.idpf.org/2007/opf}meta:")
        for elem in root.iter('{http://www.idpf.org/2007/opf}meta'):
            if elem.get('name') == 'calibre:series':
                print(f"   ✓ FOUND VIA ITER: {elem.get('content')}")
            if elem.get('name') == 'calibre:series_index':
                print(f"   ✓ FOUND INDEX VIA ITER: {elem.get('content')}")
        
        # Method 3: Find all meta tags and search through them
        print("\n3. Searching through ALL meta tags:")
        all_meta = root.findall('.//meta')
        print(f"   Found {len(all_meta)} meta tags total")
        
        series_found = False
        series_index_found = False
        
        for meta in all_meta:
            name = meta.get('name')
            content = meta.get('content')
            
            if name and 'series' in name.lower():
                print(f"   - {name} = {content}")
                
                if 'calibre:series' == name and not 'index' in name:
                    series_found = True
                    print(f"     ✓ THIS IS THE SERIES NAME!")
                
                if 'calibre:series_index' == name:
                    series_index_found = True
                    print(f"     ✓ THIS IS THE SERIES INDEX!")
        
        if not series_found:
            print("\n   ⚠️  No series name found in any meta tags")
        
        if not series_index_found:
            print("   ⚠️  No series index found in any meta tags")
        
        # Method 4: Check for dc:relation or other series fields
        print("\n4. Checking for other series-related fields:")
        
        # Some OPF files use dc:relation
        relation = root.find('.//dc:relation', ns)
        if relation is not None:
            print(f"   dc:relation: {relation.text}")
        
        # Check for belongs-to-collection
        collection = root.find(".//meta[@property='belongs-to-collection']")
        if collection is not None:
            print(f"   belongs-to-collection: {collection.text}")
        
        print("\n" + "="*60)
        print("SUMMARY:")
        print("="*60)
        
        if series_found and series_index_found:
            print("✓ Series metadata found and should be extracted correctly")
        elif series_found and not series_index_found:
            print("⚠️  Series name found but no index number")
        elif not series_found and series_index_found:
            print("⚠️  Series index found but no series name")
        else:
            print("✗ No series metadata found in this OPF file")
            print("  This book may not be part of a series, or uses a different format")
        
    except Exception as e:
        print(f"\n✗ ERROR parsing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        opf_path = sys.argv[1]
    else:
        opf_path = input("Enter path to an OPF file: ").strip().strip('"').strip("'")
    
    if Path(opf_path).exists():
        test_opf_parsing(opf_path)
    else:
        print(f"File not found: {opf_path}")