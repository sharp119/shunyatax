# shunyatax/parser.py

from bs4 import BeautifulSoup

def extract_post_urls(category_page_html):
    """
    Parses the HTML of a category page to find all 'read more' links.

    Args:
        category_page_html (str): The raw HTML content of the category page.

    Returns:
        list: A list of absolute URLs for the posts found on the page.
    """
    soup = BeautifulSoup(category_page_html, 'html.parser')
    
    # --- THIS IS THE CORRECTED LINE ---
    # Find all <a> tags where the visible text contains "read more" (case-insensitive).
    # This is the robust method from your test snippet.
    read_more_elements = soup.find_all('a', string=lambda text: text and 'read more' in text.lower())
    
    post_urls = [link['href'] for link in read_more_elements if link.has_attr('href')]
    
    print(f"Found {len(post_urls)} post URLs.")
    return post_urls