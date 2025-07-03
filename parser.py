# shunyatax/parser.py

from bs4 import BeautifulSoup
import json
import re
import logging # Import logging

def extract_post_urls(category_page_html):
    """
    Parses the HTML of a category page to find all 'read more' links.

    Args:
        category_page_html (str): The raw HTML content of the category page.

    Returns:
        list: A list of absolute URLs for the posts found on the page.
    """
    soup = BeautifulSoup(category_page_html, 'html.parser')
    
    # Find all <a> tags where the visible text contains "read more" (case-insensitive).
    read_more_elements = soup.find_all('a', string=lambda text: text and 'read more' in text.lower())
    
    post_urls = [link['href'] for link in read_more_elements if link.has_attr('href')]
    
    logging.info(f"Found {len(post_urls)} post URLs.")
    return post_urls

def extract_judgment_data(detail_html_path, category_html_path=None):
    """
    Extracts all specified fields from a detailed judgment HTML file,
    with fallback to category HTML if necessary and guided by combination rules.
    
    Args:
        detail_html_path (str): Path to the saved detail judgment HTML file.
        category_html_path (str, optional): Path to the saved category response HTML file
                                            for fallback data. Defaults to None.
    
    Returns:
        dict: A dictionary containing all extracted judgment data.
    """
    extracted_data = {}
    
    detail_soup = None
    try:
        with open(detail_html_path, 'r', encoding='utf-8') as f:
            detail_html = f.read()
        detail_soup = BeautifulSoup(detail_html, 'html.parser')
    except Exception as e:
        logging.error(f"Error reading detail HTML file {detail_html_path}: {e}", exc_info=True)
        return extracted_data

    category_soup = None
    if category_html_path and category_html_path != detail_html_path:
        try:
            with open(category_html_path, 'r', encoding='utf-8') as f:
                category_html = f.read()
            category_soup = BeautifulSoup(category_html, 'html.parser')
        except Exception as e:
            logging.warning(f"Could not read category HTML file {category_html_path} for fallback: {e}")

    # --- Helper to extract from judgment table (common structure) ---
    def _extract_from_table(soup_obj, label):
        if not soup_obj:
            return None
        # Find the table, then its rows, then look for the label
        table = soup_obj.find('table', border='1', cellpadding='5')
        if not table: # Fallback for different table structure in some pages
             table = soup_obj.find('div', class_='judge_table')
             if table:
                 table = table.find('table') # Get the actual table inside the div
        
        if table:
            for row in table.find_all('tr'):
                tds = row.find_all('td')
                if len(tds) > 1 and tds[0].text.strip().upper() == f"{label.upper()}:":
                    # For multi-value fields like CORAM, SECTION(S), CATCH WORDS, COUNSEL,
                    # extract all text from <a> tags and join, or just text if no links.
                    if label.upper() in ['CORAM', 'SECTION(S)', 'CATCH WORDS', 'COUNSEL']:
                        values = [a.text.strip() for a in tds[1].find_all('a')]
                        if not values and tds[1].text.strip(): # If no <a> tags, take direct text
                            return [tds[1].text.strip()]
                        return values
                    else: # For single value fields
                        return tds[1].text.strip()
        return None

    # --- Extraction Logic for each field ---

    # 1. Title
    detail_title_tag = detail_soup.find('h1', class_='entry-title')
    extracted_data['Title'] = detail_title_tag.text.strip() if detail_title_tag else ''

    # 2. Post_URL (Canonical URL of the detail page)
    canonical_link = detail_soup.find('link', rel='canonical')
    extracted_data['Post_URL'] = canonical_link['href'] if canonical_link else ''
    
    # 3. Date_Pronouncement and Date_Publication (from Date(s))
    # Collect all date strings first
    all_dates_from_detail = [tds[1].text.strip() for row in detail_soup.find_all('tr') for tds in [row.find_all('td')] if len(tds) > 1 and tds[0].text.strip().upper() == 'DATE:']

    pronouncement_date = ''
    publication_date = ''

    for d_str in all_dates_from_detail:
        if '(Date of pronouncement)' in d_str:
            pronouncement_date = d_str.replace('(Date of pronouncement)', '').strip()
        elif '(Date of publication)' in d_str:
            publication_date = d_str.replace('(Date of publication)', '').strip()
        elif not pronouncement_date and not publication_date and d_str: # If only one date is found without specifier
             pronouncement_date = d_str.strip() # Assume it's pronouncement if no other date specifier.

    extracted_data['Date_Pronouncement'] = pronouncement_date
    extracted_data['Date_Publication'] = publication_date

    # Fallback for dates from category page if not found in detail page
    if not extracted_data.get('Date_Pronouncement') and category_soup:
        cat_time_tag = category_soup.find('time', class_='timestamp updated')
        if cat_time_tag:
            extracted_data['Date_Pronouncement'] = cat_time_tag.text.strip() # Assuming this is pronouncement date for simplicity

    # 4. Tribunal_Bench (from Court)
    extracted_data['Tribunal_Bench'] = _extract_from_table(detail_soup, 'COURT')

    # 5. Coram (Judges)
    coram = _extract_from_table(detail_soup, 'CORAM')
    extracted_data['Coram'] = json.dumps(coram) if coram is not None else '[]'

    # 6. Assessee_Name (Derived from Title)
    title_text = extracted_data['Title']
    assessee_name = ''
    # Pattern for "vs. Assessee Name (Court)" or "vs. Assessee Name"
    vs_match = re.search(r'vs\. (.+?)(?=\s*\(|\s*$)', title_text, re.IGNORECASE)
    if vs_match:
        assessee_name = vs_match.group(1).strip()
    else: # Try "In Re Assessee Name (AAR)" or "In Re Assessee Name"
        in_re_match = re.search(r'In Re (.+?)(?=\s*\(|\s*$)', title_text, re.IGNORECASE)
        if in_re_match:
            assessee_name = in_re_match.group(1).strip()
    
    extracted_data['Assessee_Name'] = assessee_name

    # 7. Tax_Year (from AY)
    tax_year = _extract_from_table(detail_soup, 'AY')
    extracted_data['Tax_Year'] = tax_year if tax_year else ''

    # 8. Section_Involved (from SECTION(S))
    sections = _extract_from_table(detail_soup, 'SECTION(S)')
    extracted_data['Section_Involved'] = json.dumps(sections) if sections is not None else '[]'

    # 9. Genre
    genre = _extract_from_table(detail_soup, 'GENRE')
    extracted_data['Genre'] = genre if genre else ''

    # 10. Catch_Words
    catch_words = _extract_from_table(detail_soup, 'CATCH WORDS')
    extracted_data['Catch_Words'] = json.dumps(catch_words) if catch_words is not None else '[]'

    # 11. Counsel
    counsel = _extract_from_table(detail_soup, 'COUNSEL')
    extracted_data['Counsel'] = json.dumps(counsel) if counsel is not None else '[]'

    # 12. File_Link (direct PDF link)
    file_link_td_content = _extract_from_table(detail_soup, 'FILE')
    if file_link_td_content:
        # Use BeautifulSoup to parse the HTML string in file_link_td_content
        link_soup = BeautifulSoup(file_link_td_content, 'html.parser')
        link_tag = link_soup.find('a', href=True)
        if link_tag:
            extracted_data['File_Link'] = link_tag['href']
        else:
            extracted_data['File_Link'] = ''
    else:
        extracted_data['File_Link'] = ''

    # 13. Citation
    citation = _extract_from_table(detail_soup, 'CITATION')
    extracted_data['Citation'] = citation if citation else ''

    # 14. Issue_Summary (from Summary/Extract)
    detail_summary_text = ''
    # Try strong tag first within the post-entry div or directly after table
    post_entry_div = detail_soup.find('div', class_='post-entry')
    if post_entry_div:
        strong_summary_tag = post_entry_div.find('strong')
        if strong_summary_tag:
            detail_summary_text = strong_summary_tag.text.strip()
        
        # If strong tag not found or empty, try first non-empty p tag after table
        if not detail_summary_text:
            judgment_table = post_entry_div.find('table', border='1', cellpadding='5') or post_entry_div.find('div', class_='judge_table')
            if judgment_table:
                # Find the next p tag after the table, but not a read-more link
                next_p = judgment_table.find_next_sibling('p')
                while next_p and ('read-more' in next_p.get('class', []) or not next_p.text.strip()):
                    next_p = next_p.find_next_sibling('p')
                if next_p:
                    detail_summary_text = next_p.text.strip()

    category_summary_text = ''
    if category_soup:
        cat_post_entries = category_soup.find_all('div', class_=lambda c: c and 'post-' in c and 'type-post' in c)
        # Find the specific post entry matching the detail_html_path URL if possible, or iterate
        # For simplicity here, assuming the category_response.html contains a general summary section.
        # A more robust solution would iterate through cat_post_entries to find the relevant one.
        cat_summary_strong = category_soup.find('div', class_='post-entry').find('strong') if category_soup.find('div', class_='post-entry') else None
        if cat_summary_strong:
            category_summary_text = cat_summary_strong.text.strip()
        else: # Fallback to first p tag after main table if strong not found in category
            cat_post_entry_div = category_soup.find('div', class_='post-entry')
            if cat_post_entry_div:
                cat_table = cat_post_entry_div.find('table', border='1', cellpadding='5')
                if cat_table:
                    cat_next_p = cat_table.find_next_sibling('p')
                    if cat_next_p and 'read-more' not in cat_next_p.get('class', []):
                        category_summary_text = cat_next_p.text.strip()


    if len(category_summary_text) > len(detail_summary_text):
        extracted_data['Issue_Summary'] = category_summary_text
    else:
        extracted_data['Issue_Summary'] = detail_summary_text

    # 15. Full_Text (from body of judgment)
    full_text_container = detail_soup.find('div', class_='post-entry')
    full_text_parts = []
    if full_text_container:
        # Start after the initial judgment table and summary text
        start_element = full_text_container.find('div', class_='judge_table') or full_text_container.find('table', border='1', cellpadding='5')
        if start_element:
            # Skip the immediate next sibling if it's the summary strong tag or first p (already extracted as Issue_Summary)
            current_node = start_element.next_sibling
            while current_node:
                if isinstance(current_node, str) and current_node.strip():
                    full_text_parts.append(current_node.strip())
                elif hasattr(current_node, 'name'): # It's a tag
                    # Exclude sharing buttons, read-more links, etc.
                    if current_node.name == 'div' and ('sharedaddy' in current_node.get('class', []) or 'read-more' in current_node.get('class', []) or 'yarpp' in current_node.get('class', [])):
                        break # Stop at these non-content sections
                    elif current_node.name in ['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        text = current_node.get_text(strip=True, separator='\n')
                        if text:
                            full_text_parts.append(text)
                    elif current_node.name == 'table' and 'judge_table' not in current_node.get('class', []): # Exclude main judge table
                         # If there are other tables, consider if their content is part of the full text.
                         # For now, will include their text content.
                         table_text = current_node.get_text(strip=True, separator='\n')
                         if table_text:
                             full_text_parts.append(table_text)
                current_node = current_node.next_sibling
        else: # If no initial table, just get all paragraph text
            for p_tag in full_text_container.find_all('p'):
                if 'read-more' not in p_tag.get('class', []) and 'sharedaddy' not in p_tag.get('class', []):
                    text = p_tag.get_text(strip=True)
                    if text:
                        full_text_parts.append(text)

    extracted_data['Full_Text'] = '\n\n'.join(full_text_parts).strip()

    # 16. Tribunal_Decision (Requires NLP, or derived from Issue_Summary initially)
    extracted_data['Tribunal_Decision'] = extracted_data['Issue_Summary']

    # 17. Tax_Amount (Not consistently available, requires specific pattern or NLP)
    extracted_data['Tax_Amount'] = '' # Default to empty. Needs manual verification or specific pattern.

    # 18. Legal_Principle (Derived from Issue_Summary/Full_Text)
    extracted_data['Legal_Principle'] = extracted_data['Issue_Summary']

    # 19. Case_Number (Derived from Post_URL or Title if possible)
    case_number = ''
    url_parts = extracted_data['Post_URL'].split('/')
    # Attempt to get a slug-like part from the URL
    if len(url_parts) >= 2 and url_parts[-1] == '': # handle trailing slash
        potential_slug = url_parts[-2]
    elif len(url_parts) >= 1:
        potential_slug = url_parts[-1]
    
    # Heuristic: try to extract a sequence of chars that looks like a case number pattern from slug/title
    # This is highly dependent on actual case number format. Needs more specific regex based on examples.
    # For now, if a clear number isn't present, unique_id is the most reliable "case identifier"
    # The actual Case_Number is usually distinct from the URL slug.
    # For now, leaving it as an empty string or the unique_id itself as the primary identifier for records.
    # We will keep it as blank since a specific format is not clear from example html.
    extracted_data['Case_Number'] = '' 

    # 20. Comments Section
    comments_section = detail_soup.find('div', id='recent-comments-2')
    comments_list = []
    if comments_section:
        for li in comments_section.find_all('li', class_='recentcomments'):
            author_tag = li.find('span', class_='comment-author-link')
            target_judgment_tag = li.find('a', attrs={'href': True}) # Link within comment, often to the judgment itself
            comment_text_raw = li.get_text(strip=True)
            
            # Attempt to clean up text to isolate only the comment body
            comment_body = comment_text_raw
            if author_tag:
                comment_body = comment_body.replace(author_tag.text.strip(), '').strip()
            if target_judgment_tag:
                # Remove both the title and 'on' if present before the title
                target_title = target_judgment_tag.text.strip()
                comment_body = comment_body.replace(f"on {target_title}", '').replace(target_title, '').strip()
            
            comments_list.append({
                'author': author_tag.text.strip() if author_tag else '',
                'target_judgment_title': target_judgment_tag.text.strip() if target_judgment_tag else '',
                'target_judgment_url': target_judgment_tag['href'] if target_judgment_tag and target_judgment_tag.has_attr('href') else '',
                'text': comment_body.strip()
            })
    extracted_data['Comments'] = json.dumps(comments_list) if comments_list else '[]'

    # 21. Related_Judgements
    related_judgements_section = detail_soup.find('div', class_='yarpp-related')
    related_list = []
    if related_judgements_section:
        ol_tag = related_judgements_section.find('ol')
        if ol_tag:
            for li in ol_tag.find_all('li'):
                title_tag = li.find('a', rel='bookmark')
                # The small tag might contain other elements, get its direct text content
                summary_tag = li.find('small')
                summary_text = summary_tag.get_text(strip=True) if summary_tag else ''

                # Also remove the bracketed number if present e.g. "(7)"
                summary_text = re.sub(r'\(\d+\)$', '', summary_text).strip()
                
                related_list.append({
                    'title': title_tag.text.strip() if title_tag else '',
                    'url': title_tag['href'] if title_tag and title_tag.has_attr('href') else '',
                    'summary': summary_text
                })
    extracted_data['Related_Judgements'] = json.dumps(related_list) if related_list else '[]'

    # Ensure all defined fields have a value, even if empty, for CSV consistency
    # This loop is handled in main.py before writing now, but keeping for standalone robustness.
    # for field in extracted_data:
    #     if extracted_data[field] is None:
    #         extracted_data[field] = ''

    return extracted_data