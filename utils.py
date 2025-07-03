# shunyatax/utils.py

import os
import csv
import time
import random
import hashlib
import json
import logging # Import the logging module

# Configure logging
def setup_logging():
    log_file = 'project.log'
    # Clear log file from previous run for cleaner output, or change to 'a' to append
    if os.path.exists(log_file):
        open(log_file, 'w').close() 
        
    logging.basicConfig(
        level=logging.INFO, # Set overall logging level to INFO
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file), # Log to a file
            logging.StreamHandler()        # Log to console
        ]
    )
    logging.getLogger('tqdm').setLevel(logging.WARNING) # Suppress tqdm's own logging messages

def generate_unique_id(url):
    """Generates a unique ID based on the URL."""
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def load_ledger():
    """Loads all entries from ledger.csv."""
    ledger_file = 'ledger.csv'
    entries = []
    if os.path.exists(ledger_file) and os.path.getsize(ledger_file) > 0:
        with open(ledger_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Check if 'unique_id' is in the fieldnames to avoid KeyError later
            if 'unique_id' not in reader.fieldnames:
                logging.error(f"Ledger file '{ledger_file}' is missing 'unique_id' column in header. Please ensure it's correctly formatted.")
                return [] # Return empty list if header is bad
            for row in reader:
                entries.append(row)
    logging.info(f"Loaded {len(entries)} entries from ledger.")
    return entries

def load_progress():
    """Loads progress from progress_tracker.csv."""
    progress_file = 'progress_tracker.csv'
    progress = {}
    if os.path.exists(progress_file) and os.path.getsize(progress_file) > 0:
        with open(progress_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header: # Ensure header exists
                for row in reader:
                    if len(row) == 2:
                        progress[row[0]] = int(row[1])
    logging.info("Progress loaded.")
    return progress

def update_progress(category_name, page_number):
    """Updates the progress_tracker.csv for a given category."""
    progress_file = 'progress_tracker.csv'
    progress = load_progress()
    progress[category_name] = page_number
    
    with open(progress_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'last_page'])
        for cat, page in progress.items():
            writer.writerow([cat, page])
    logging.info(f"Updated progress for {category_name} to page {page_number}")

# Removed log_error functions, use logging.error directly

def get_random_sleep_interval():
    """Returns a random sleep interval between 2 and 8 seconds."""
    interval = random.uniform(2, 8)
    logging.debug(f"Sleeping for {interval:.2f} seconds.")
    return interval

def add_to_ledger(unique_id, file_path, post_url):
    """Appends an entry to the ledger CSV."""
    ledger_file = 'ledger.csv'
    mode = 'a' if os.path.exists(ledger_file) and os.path.getsize(ledger_file) > 0 else 'w' # Check if file has content
    with open(ledger_file, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(['unique_id', 'file_path', 'post_url'])
        writer.writerow([unique_id, file_path, post_url])
    logging.debug(f"Added to ledger: {unique_id}") # Use logging.debug for less critical info
