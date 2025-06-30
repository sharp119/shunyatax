# shunyatax/fetcher.py

import time
import requests
from fake_useragent import UserAgent
# Corrected import section
from config import MAX_RETRIES, REQUEST_TIMEOUT, ERROR_LOG_FILE
from utils import log_error

ua = UserAgent()

def fetch_url(url):
    """
    Fetches a URL with retries, exponential backoff, and a random user-agent.
    
    Args:
        url (str): The URL to fetch.

    Returns:
        requests.Response: The response object on success, or None on failure.
    """
    headers = {'User-Agent': ua.random}
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.exceptions.HTTPError as e:
            # A 404 is a definitive "not found" and should not be retried.
            if e.response.status_code == 404:
                print(f"URL not found (404): {url}")
                return e.response # Return the response object to check status in main
            print(f"HTTP Error for {url}: {e}. Retrying...")
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}. Attempt {attempt + 1}/{MAX_RETRIES}")
            
        # Exponential backoff
        time.sleep(2 ** attempt)

    log_error(ERROR_LOG_FILE, url, "Failed to fetch after all retries.")
    return None