import csv
import os
import shutil # For safely replacing the file

def fix_ledger_csv(file_path='ledger.csv'):
    """
    Checks if ledger.csv has the correct header and adds it if missing.
    Assumes the correct header is ['unique_id', 'file_path', 'post_url'].
    """
    expected_header = ['unique_id', 'file_path', 'post_url']
    temp_file_path = f"{file_path}.temp"
    header_added = False

    print(f"Checking ledger file: {file_path}")

    try:
        # Check if file exists and has content
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            print(f"'{file_path}' is empty or does not exist. Creating with header.")
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(expected_header)
            print(f"'{file_path}' created with header. Please run Phase 1 to populate it.")
            return

        with open(file_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            first_line = next(reader, None) # Read the first line

            if first_line == expected_header:
                print(f"'{file_path}' already has the correct header. No fix needed.")
                return

            # If header is incorrect or missing, prepare to write new file with correct header
            with open(temp_file_path, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(expected_header) # Write the correct header
                header_added = True

                if first_line is not None: # If there was a first line (but it was wrong header)
                    # Try to write it back as data if it's not our expected header.
                    # This assumes that if the first_line is *not* the expected header,
                    # it might be a data row or a malformed header that should be treated as data.
                    # For robust recovery, a more complex parser might be needed here,
                    # but for typical missing header, this works.
                    if first_line != expected_header and len(first_line) == len(expected_header):
                         writer.writerow(first_line)
                    elif first_line != expected_header and len(first_line) != len(expected_header):
                        print(f"Warning: Original first line '{first_line}' does not match expected header length. Skipping as potentially malformed.")
                    
                # Write the rest of the lines
                for row in reader:
                    writer.writerow(row)

        # Replace original file with the corrected one
        shutil.move(temp_file_path, file_path)
        print(f"Successfully fixed '{file_path}' by adding/correcting the header.")

    except FileNotFoundError:
        print(f"Error: '{file_path}' not found. Please ensure it exists.")
    except Exception as e:
        print(f"An error occurred during ledger repair: {e}")
        # Clean up temp file if error occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    fix_ledger_csv()