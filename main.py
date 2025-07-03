import argparse
import os
import csv
import json
import time
import logging
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Import project modules
import config
import fetcher
import utils
import parser

# Define a new constant for the extracted data file base name
EXTRACTED_CSV_BASENAME = 'extracted' # Will become extracted_1.csv, extracted_2.csv etc.

# Helper function to encapsulate parsing for multiprocessing
def _process_single_entry_for_extraction(entry_data):
    """
    Worker function for ProcessPoolExecutor in Phase 2.
    Parses a single HTML file and returns its extracted data.
    """
    unique_id = entry_data['unique_id']
    html_file_path = entry_data['file_path']
    # Reconstruct category_response_path for parser
    category_folder = os.path.dirname(html_file_path)
    category_response_path = os.path.join(category_folder, 'category_response.html')
    
    try:
        extracted_data = parser.extract_judgment_data(html_file_path, category_response_path)
        extracted_data['unique_id'] = unique_id
        # logging.debug(f"Successfully extracted data for {unique_id}") # Logged by main process
        return extracted_data
    except Exception as e:
        logging.error(f"Error extracting data from {html_file_path} (unique_id: {unique_id}): {e}", exc_info=True)
        return None # Return None if extraction fails

def run_phase1_data_collection():
    """
    Orchestrates the data collection phase (Phase 1).
    """
    logging.info("Starting Phase 1: Data Collection...")
    
    progress = utils.load_progress()

    for category_name, base_url in config.CATEGORIES.items():
        logging.info(f"\nProcessing category: {category_name}")
        current_page = progress.get(category_name, 1)
        
        while True:
            category_url = f"{base_url}/page/{current_page}/" if current_page > 1 else base_url
            category_folder = os.path.join(config.DATA_DIR, category_name, f"page_{current_page}")
            
            os.makedirs(category_folder, exist_ok=True)
            
            category_file_path = os.path.join(category_folder, 'category_response.html')

            logging.info(f"Fetching category page {current_page} for {category_name} from {category_url}")
            try:
                category_html_content = fetcher.fetch_html(category_url, category_file_path)
                
                if not category_html_content or "404 Not Found" in category_html_content:
                    logging.info(f"No more pages for {category_name} or error fetching page {current_page}. Stopping.")
                    break

                read_more_links = []
                soup = BeautifulSoup(category_html_content, 'html.parser')
                post_entries = soup.find_all('div', class_=lambda c: c and 'post-' in c and 'type-post' in c)

                for entry_div in post_entries:
                    title_link_tag = entry_div.find('h2', class_='entry-title').find('a')
                    if title_link_tag and title_link_tag.has_attr('href'):
                        post_url = title_link_tag['href']
                        unique_id = utils.generate_unique_id(post_url)
                        read_more_links.append({'title': title_link_tag.text.strip(), 'url': post_url, 'unique_id': unique_id})

                if not read_more_links and current_page > 1:
                    logging.info(f"No more posts found on page {current_page} for {category_name}. Stopping.")
                    break

                with tqdm(total=len(read_more_links), desc=f"Fetching posts for {category_name} Page {current_page}", unit="post") as pbar:
                    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
                        futures = []
                        for item in read_more_links:
                            futures.append(executor.submit(fetcher.fetch_read_more_page, item['url'], category_folder, item['unique_id']))
                        
                        for future in as_completed(futures):
                            result = future.result()
                            if result:
                                utils.add_to_ledger(result['unique_id'], result['file_path'], result['url'])
                            pbar.update(1)

                utils.update_progress(category_name, current_page)
                current_page += 1
                time.sleep(utils.get_random_sleep_interval())
                
            except Exception as e:
                logging.error(f"Error in Phase 1 for {category_url}: {e}", exc_info=True)
                break


def run_phase2_data_extraction():
    """
    Orchestrates the data extraction and cleaning phase (Phase 2),
    processing each category separately and paginating output CSVs.
    """
    logging.info("Starting Phase 2: Data Extraction and Cleaning...")

    all_ledger_entries = utils.load_ledger()
    if not all_ledger_entries:
        logging.warning("Ledger is empty. No files to process for Phase 2. Please run Phase 1 first.")
        return

    # Define CSV header based on all required fields
    fieldnames = [
        'unique_id', 'Case_Number', 'Title', 'Post_URL', 'Date_Pronouncement', 'Date_Publication',
        'Tribunal_Bench', 'Coram', 'Assessee_Name', 'Tax_Year', 'Section_Involved', 'Genre',
        'Catch_Words', 'Counsel', 'File_Link', 'Citation', 'Issue_Summary',
        'Tribunal_Decision', 'Tax_Amount', 'Legal_Principle',
        'Full_Text', 'Comments', 'Related_Judgements'
    ]

    # Group ledger entries by category
    categorized_entries = {}
    for entry in all_ledger_entries:
        # Assuming category name can be derived from file_path, e.g., 'data/CATEGORY_NAME/page_N/...'
        path_parts = entry['file_path'].split(os.sep)
        # Find the category name, assuming structure: data/category_name/...
        if len(path_parts) > 1 and path_parts[0] == 'data': # 'data' is the root data folder
            category_name = path_parts[1]
        else:
            category_name = "UnknownCategory" # Fallback if path structure is unexpected
            logging.warning(f"Could not determine category for {entry['file_path']}. Assigning to {category_name}.")

        if category_name not in categorized_entries:
            categorized_entries[category_name] = []
        categorized_entries[category_name].append(entry)

    num_processes = multiprocessing.cpu_count()
    logging.info(f"Using {num_processes} processes for parallel extraction per category.")

    for category_name, entries_in_category in categorized_entries.items():
        logging.info(f"\nProcessing category: {category_name} ({len(entries_in_category)} entries)")
        
        category_output_dir = os.path.join(config.OUTPUT_DIR, category_name)
        os.makedirs(category_output_dir, exist_ok=True)

        # Track processed IDs for this category for resume
        processed_ids_in_category = set()
        # Find the last processed file and entry count to resume pagination correctly
        last_csv_index = 0
        last_entry_count = 0
        
        # This part requires robust scanning of existing CSVs to resume correctly if needed
        # For simplicity, if previous files exist, we will just append to the last one
        # or create new ones if current count exceeds 100.
        # A more robust solution would iterate through existing CSVs, count rows, and find last index.
        # For now, let's just make sure we don't duplicate processing logic.
        
        # To avoid re-processing, we need to check all existing CSVs for this category.
        existing_csv_files = sorted([f for f in os.listdir(category_output_dir) if f.startswith(EXTRACTED_CSV_BASENAME) and f.endswith('.csv')])
        for existing_csv in existing_csv_files:
            try:
                full_path = os.path.join(category_output_dir, existing_csv)
                with open(full_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames and 'unique_id' in reader.fieldnames:
                        for row in reader:
                            if 'unique_id' in row:
                                processed_ids_in_category.add(row['unique_id'])
                        
                        # Update last_csv_index and last_entry_count based on last file
                        match = re.search(r'_(\d+)\.csv$', existing_csv)
                        if match:
                            idx = int(match.group(1))
                            if idx > last_csv_index:
                                last_csv_index = idx
                                # Count rows in this file
                                with open(full_path, 'r', newline='', encoding='utf-8') as temp_f:
                                    last_entry_count = sum(1 for line in temp_f) - 1 # -1 for header
                                if last_entry_count == 100: # If last file is full, next starts a new one
                                    last_entry_count = 0
                                    last_csv_index += 1
                                    
            except Exception as e:
                logging.warning(f"Error reading existing CSV {full_path} for resume: {e}")
        
        logging.info(f"Resuming for {category_name}: Found {len(processed_ids_in_category)} already processed. Starting CSV index: {last_csv_index}, current entry count in last file: {last_entry_count}.")

        entries_to_process = [entry for entry in entries_in_category if entry['unique_id'] not in processed_ids_in_category]

        if not entries_to_process:
            logging.info(f"All entries in {category_name} already processed. Skipping category.")
            continue

        current_output_csv_index = last_csv_index
        current_csv_entry_count = last_entry_count
        current_outfile = None
        current_writer = None

        try:
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                # Use as_completed to process results as they become available
                futures = {executor.submit(_process_single_entry_for_extraction, entry): entry['unique_id'] for entry in entries_to_process}
                
                with tqdm(total=len(entries_to_process), desc=f"Extracting & Writing {category_name}", unit="file") as pbar:
                    for future in as_completed(futures):
                        extracted_data = future.result() # This is the result from the worker process
                        original_unique_id = futures[future] # Get original unique_id for logging

                        if extracted_data:
                            # Manage CSV file pagination
                            if current_csv_entry_count == 0:
                                # Close previous file if open
                                if current_outfile:
                                    current_outfile.close()
                                logging.info(f"Starting new CSV file for {category_name}: {EXTRACTED_CSV_BASENAME}_{current_output_csv_index + 1}.csv")
                                current_output_csv_index += 1
                                output_file_name = f"{EXTRACTED_CSV_BASENAME}_{current_output_csv_index}.csv"
                                current_file_path = os.path.join(category_output_dir, output_file_name)
                                
                                file_had_content = os.path.exists(current_file_path) and os.path.getsize(current_file_path) > 0
                                
                                current_outfile = open(current_file_path, 'a', newline='', encoding='utf-8')
                                current_writer = csv.DictWriter(current_outfile, fieldnames=fieldnames)
                                
                                if not file_had_content:
                                    current_writer.writeheader()
                                logging.debug(f"Opened CSV {output_file_name} for writing.")
                                current_csv_entry_count = 0 # Reset count for new file

                            # Ensure all fieldnames are present in extracted_data before writing
                            for field in fieldnames:
                                if field not in extracted_data:
                                    extracted_data[field] = ''
                            
                            current_writer.writerow(extracted_data)
                            current_csv_entry_count += 1
                            pbar.update(1)
                            # logging.debug(f"Wrote {original_unique_id} to CSV. Count: {current_csv_entry_count}/{config.MAX_ENTRIES_PER_CSV}.")
                            if current_csv_entry_count >= config.MAX_ENTRIES_PER_CSV: # Check if limit reached
                                logging.info(f"CSV file {EXTRACTED_CSV_BASENAME}_{current_output_csv_index}.csv reached {config.MAX_ENTRIES_PER_CSV} entries.")
                                current_outfile.close()
                                current_outfile = None
                                current_writer = None
                                current_csv_entry_count = 0 # Prepare for next file
                        else:
                            logging.warning(f"Skipping writing data for {original_unique_id} due to extraction errors.")

        finally:
            if current_outfile: # Ensure the last opened file is closed
                current_outfile.close()
                logging.info(f"Last CSV file for {category_name} closed.")
            
    logging.info("Phase 2 complete: All categories processed.")


def main():
    utils.setup_logging()

    parser_main = argparse.ArgumentParser(description="Run ITAT Judgment Scraper and Extractor.")
    parser_main.add_argument('phase', choices=['1', '2'], help="Choose which phase to run: '1' for Data Collection, '2' for Data Extraction.")
    args = parser_main.parse_args()

    try:
        if args.phase == '1':
            run_phase1_data_collection()
        elif args.phase == '2':
            # Add a new constant for max entries per CSV
            if not hasattr(config, 'MAX_ENTRIES_PER_CSV'):
                config.MAX_ENTRIES_PER_CSV = 100 # Default if not in config.py
                logging.warning(f"MAX_ENTRIES_PER_CSV not found in config.py, defaulting to {config.MAX_ENTRIES_PER_CSV}")
            run_phase2_data_extraction()
    except Exception as e:
        logging.critical(f"An unhandled error occurred in main execution: {e}", exc_info=True)


if __name__ == "__main__":
    main()