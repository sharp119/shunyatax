# shunyatax/main.py

import os
from config import (
    CATEGORIES, CATEGORY_URL_TEMPLATE, CATEGORY_PAGINATION_URL_TEMPLATE,
    LEDGER_FILE, PROGRESS_FILE, ERROR_LOG_FILE, DATA_FOLDER
)
import utils
import fetcher
import parser

def scrape_category(category):
    """Manages the scraping of a single category, including pagination."""
    progress = utils.load_progress(PROGRESS_FILE)
    start_page = progress.get(category, 1)
    page_num = start_page
    
    print(f"\n--- Starting category: {category} from page: {page_num} ---")

    while True:
        if page_num == 1:
            page_url = CATEGORY_URL_TEMPLATE.format(category=category)
        else:
            page_url = CATEGORY_PAGINATION_URL_TEMPLATE.format(category=category, page=page_num)
        
        print(f"\nFetching category page: {page_url}")
        response = fetcher.fetch_url(page_url)

        if not response or response.status_code == 404:
            print(f"No more pages found for category '{category}'. Moving to the next.")
            break

        # Define path for the category page response and save it
        page_folder = os.path.join(DATA_FOLDER, category, f"page_{page_num}")
        category_response_path = os.path.join(page_folder, "category_response.html")
        utils.save_html(category_response_path, response.text)

        # Extract post URLs from the saved category page
        post_urls = parser.extract_post_urls(response.text)
        if not post_urls:
            print(f"No 'read more' links found on {page_url}. Assuming end of category.")
            break
            
        for post_url in post_urls:
            print(f"Fetching post: {post_url}")
            post_response = fetcher.fetch_url(post_url)
            if post_response:
                unique_id = utils.generate_unique_id()
                post_filepath = os.path.join(page_folder, f"{unique_id}.html")
                
                utils.save_html(post_filepath, post_response.text)
                utils.update_ledger(LEDGER_FILE, unique_id, post_filepath, post_url)

        # After successfully processing all posts on the page
        utils.update_progress(PROGRESS_FILE, category, page_num)
        page_num += 1
        utils.polite_pause()

def main():
    """Main function to orchestrate the scraping process for all categories."""
    print("Starting Shunyatax Scraper...")
    for category in CATEGORIES:
        scrape_category(category)
    print("\n--- All categories have been processed. ---")

if __name__ == "__main__":
    main()
