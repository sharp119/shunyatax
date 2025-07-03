# shunyatax/fetcher.py

import requests
import os
import time
import logging # Import logging

# Assuming config.py is in the same directory or accessible via PYTHONPATH
import config

def fetch_html(url, save_path):
    """
    Fetches HTML content from a URL and saves it to a file.
    Includes retry logic.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(config.MAX_RETRIES):
        try:
            logging.info(f"Attempt {attempt + 1}: Fetching {url}")
            response = requests.get(url, headers=headers, timeout=config.RETRY_DELAY_SECONDS * 2) # Set a reasonable timeout
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logging.info(f"Successfully fetched and saved: {save_path}")
            return response.text # Return content for parsing links in main.py
        except requests.exceptions.HTTPError as e:
            logging.warning(f"HTTP error fetching {url}: {e}")
            if response.status_code == 404:
                logging.info(f"Page not found (404) for {url}. Assuming end of pagination.")
                return None # Return None for 404 to signal end of pages
            elif response.status_code == 429:
                logging.warning(f"Too many requests (429) for {url}. Retrying with delay.")
                time.sleep(config.RETRY_DELAY_SECONDS * (attempt + 1)) # Exponential backoff
            else:
                logging.error(f"Non-retryable HTTP error for {url}: {e}", exc_info=True)
                break # Break for other HTTP errors
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"Connection error fetching {url}: {e}. Retrying.")
            time.sleep(config.RETRY_DELAY_SECONDS * (attempt + 1))
        except requests.exceptions.Timeout as e:
            logging.warning(f"Timeout error fetching {url}: {e}. Retrying.")
            time.sleep(config.RETRY_DELAY_SECONDS * (attempt + 1))
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching {url}: {e}", exc_info=True)
            break # Break for unexpected errors
    logging.error(f"Failed to fetch {url} after {config.MAX_RETRIES} attempts.")
    return None

def fetch_read_more_page(url, category_folder, unique_id):
    """
    Fetches a single 'read more' page and saves it.
    """
    save_path = os.path.join(category_folder, f'{unique_id}.html')
    if os.path.exists(save_path):
        logging.info(f"File already exists: {save_path}. Skipping fetch.")
        return {'unique_id': unique_id, 'file_path': save_path, 'url': url} # Return existing info
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(config.MAX_RETRIES):
        try:
            logging.info(f"Attempt {attempt + 1}: Fetching read more page {url}")
            response = requests.get(url, headers=headers, timeout=config.RETRY_DELAY_SECONDS * 2)
            response.raise_for_status()
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logging.info(f"Successfully fetched and saved: {save_path}")
            return {'unique_id': unique_id, 'file_path': save_path, 'url': url}
        except requests.exceptions.RequestException as e: # Catch all requests exceptions
            logging.warning(f"Error fetching {url}: {e}. Retrying.")
            time.sleep(config.RETRY_DELAY_SECONDS * (attempt + 1))
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching read more page {url}: {e}", exc_info=True)
            break # Break for unexpected errors
    logging.error(f"Failed to fetch read more page {url} after {config.MAX_RETRIES} attempts.")
    return None