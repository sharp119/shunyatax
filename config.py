# shunyatax/config.py

import os

# -- Categories and URLs --
# Categories to be scraped, matching the URL slugs
CATEGORIES = [
    'aar',
    'all-judgements',
    'high-court',
    'others',
    'supreme-court',
    'tribunal'
]

# Base URL for the website
BASE_URL = "https://itatonline.org/archives"

# URL template for the first page of a category
CATEGORY_URL_TEMPLATE = f"{BASE_URL}/category/{{category}}/"

# URL template for paginated category pages (page 2 and beyond)
CATEGORY_PAGINATION_URL_TEMPLATE = f"{BASE_URL}/category/{{category}}/page/{{page}}/"

# -- Fetching Parameters --
# Maximum number of retries for a failed HTTP request
MAX_RETRIES = 3

# Timeout in seconds for HTTP requests
REQUEST_TIMEOUT = 15

# Minimum and maximum delay in seconds between fetching pages for rate limiting
MIN_RATE_LIMIT_DELAY = 2
MAX_RATE_LIMIT_DELAY = 8

# Maximum number of concurrent workers for Phase 1
MAX_WORKERS = 5

# -- File and Folder Configuration --
# Base directory for data storage (relative to project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'extracted_data')

# Name of the CSV file to track all scraped posts
LEDGER_FILE = "ledger.csv"

# Name of the CSV file to track scraping progress for each category
PROGRESS_FILE = "progress_tracker.csv"

# Name of the file to log errors
ERROR_LOG_FILE = "error_log.txt"

# Folder to store the raw HTML responses
DATA_FOLDER = "data"

# Define extracted data file name
EXTRACTED_DATA_FILE = 'extracted_judgments.csv'

MAX_ENTRIES_PER_CSV = 100