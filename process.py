"""
process.py

Process and clean CSV data for database upload.
Raw fields are loaded as-is; NULL is stored wherever a value is absent.

Usage
-----
    python process.py --input sbdb_query_results.csv
    python process.py --input sbdb_query_results.csv --skip-load
    python process.py --download
"""

import csv
import os
import sys

# Output files for each table
OUTPUT_FILES = {
    'NEO': 'data/neo_cleaned.csv',
    'PhysicalProperties': 'data/physical_properties_cleaned.csv',
    'OrbitalElements': 'data/orbital_elements_cleaned.csv',
    'ObservationRecord': 'data/observation_record_cleaned.csv'
}

# Field mappings from source CSV to target tables
FIELD_MAPPINGS = {
    'NEO': {
        'fields': ['spkid', 'full_name', 'pha', 'class'],
        'transform': lambda row: (
            row.get('spkid', '').strip(),
            row.get('full_name', '').strip()[:120],
            'Y' if row.get('pha', '').strip().upper() == 'Y' else 'N',
            row.get('class', '').strip()
        )
    },
    'PhysicalProperties': {
        'fields': ['spkid', 'H', 'diameter'],
        'transform': lambda row: (
            row.get('spkid', '').strip(),
            row.get('H', '').strip() or '\\N',
            row.get('diameter', '').strip() or '\\N'
        )
    },
    'OrbitalElements': {
        'fields': ['spkid', 'e', 'q', 'i', 'moid', 'moid_ld'],
        'transform': lambda row: (
            row.get('spkid', '').strip(),
            row.get('e', '').strip() or '\\N',
            row.get('q', '').strip() or '\\N',
            row.get('i', '').strip() or '\\N',
            row.get('moid', '').strip() or '\\N',
            row.get('moid_ld', '').strip() or '\\N'
        )
    },
    'ObservationRecord': {
        'fields': ['spkid', 'data_arc', 'condition_code'],
        'transform': lambda row: (
            row.get('spkid', '').strip(),
            row.get('data_arc', '').strip() or '\\N',
            row.get('condition_code', '').strip() or '\\N'
        )
    }
}

def clean_csv(input_file='data/sbdb_query_results.csv'):
    """Process raw CSV and create cleaned files for each table."""
    
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize output files
    file_handles = {}
    csv_writers = {}
    stats = {'total': 0, 'neo': 0, 'non_neo': 0, 'missing_spkid': 0, 'errors': 0}
    
    try:
        # Create output files and writers
        for table_name, output_path in OUTPUT_FILES.items():
            file_handles[table_name] = open(output_path, 'w', newline='', encoding='utf-8')
            csv_writers[table_name] = csv.writer(file_handles[table_name])
            # Write headers
            csv_writers[table_name].writerow(FIELD_MAPPINGS[table_name]['fields'])
        
        # Process input CSV
        with open(input_file, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                stats['total'] += 1
                
                # Skip non-NEOs
                if row.get('neo', '').strip().upper() == 'N':
                    stats['non_neo'] += 1
                    continue
                
                # Skip rows without spkid (don't count as error)
                spkid = row.get('spkid', '').strip()
                if not spkid:
                    stats['missing_spkid'] += 1
                    continue
                
                try:
                    # Write to each table
                    for table_name, mapping in FIELD_MAPPINGS.items():
                        transformed_row = mapping['transform'](row)
                        csv_writers[table_name].writerow(transformed_row)
                    
                    stats['neo'] += 1
                        
                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] <= 10:  # Limit error output
                        print(f"\n[ERROR] Line {row_num} (spkid={spkid}): {e}")
        
    finally:
        # Close all output files
        for handle in file_handles.values():
            handle.close()
    
    # Print statistics
    print(f"Total rows read:        {stats['total']:>8,}")
    print(f"Non-NEOs skipped:       {stats['non_neo']:>8,}")
    print(f"Missing spkid (skipped):{stats['missing_spkid']:>8,}")
    print(f"NEOs processed:         {stats['neo']:>8,}")
    print(f"Errors encountered:     {stats['errors']:>8,}")
    print("\nOutput files created:")
    for table_name, output_path in OUTPUT_FILES.items():
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"  {output_path:30s}")


def main():
    """Main entry point."""
    clean_csv()

if __name__ == '__main__':
    main()