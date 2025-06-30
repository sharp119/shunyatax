# shunyatax/utils.py

import os
import csv
import time
import random
import uuid
from config import MIN_RATE_LIMIT_DELAY, MAX_RATE_LIMIT_DELAY

def generate_unique_id():
    """Generates a unique hexadecimal ID for a post."""
    return uuid.uuid4().hex

def save_html(filepath, content):
    """Saves HTML content to a file, creating parent directories if needed."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully saved to {filepath}")
    except IOError as e:
        print(f"Error saving file {filepath}: {e}")

def update_ledger(ledger_file, unique_id, file_path, post_url):
    """Appends a new record to the ledger CSV file."""
    try:
        with open(ledger_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header if the file is new/empty
            if f.tell() == 0:
                writer.writerow(['unique_id', 'file_path', 'post_url'])
            writer.writerow([unique_id, file_path, post_url])
    except IOError as e:
        print(f"Error updating ledger {ledger_file}: {e}")

def load_progress(progress_file):
    """Loads the last scraped page for each category from the progress tracker."""
    if not os.path.exists(progress_file):
        return {}
    
    progress = {}
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Skip header
            for row in reader:
                if row:
                    progress[row[0]] = int(row[1])
    except (IOError, IndexError) as e:
        print(f"Could not read progress file {progress_file}, starting from scratch. Error: {e}")
        return {}
        
    return progress

def update_progress(progress_file, category, page_number):
    """Updates the progress tracker with the last successfully scraped page."""
    progress = load_progress(progress_file)
    progress[category] = page_number
    
    try:
        with open(progress_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['category', 'last_page'])
            for cat, page in progress.items():
                writer.writerow([cat, page])
    except IOError as e:
        print(f"Error updating progress file {progress_file}: {e}")

def log_error(error_log_file, url, message):
    """Logs a persistent fetch error to the error log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(error_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} - URL: {url} - Error: {message}\n")
    except IOError as e:
        print(f"Critical error: Could not write to log file {error_log_file}. Error: {e}")

def polite_pause():
    """Pauses execution for a random interval to be polite to the server."""
    delay = random.uniform(MIN_RATE_LIMIT_DELAY, MAX_RATE_LIMIT_DELAY)
    print(f"Pausing for {delay:.2f} seconds...")
    time.sleep(delay)
