# Brainstorm
================

## URLs

### AAR

* https://itatonline.org/archives/category/aar/?judges&section&counsel&court&catchwords&genre
* https://itatonline.org/archives/category/aar/page/2/?judges&section&counsel&court&catchwords&genre

### All Judgements

* https://itatonline.org/archives/category/all-judgements/?judges&section&counsel&court&catchwords&genre
* https://itatonline.org/archives/category/all-judgements/page/2/?judges&section&counsel&court&catchwords&genre

## Plan

### Pagination & Categories

* The URLs above show how pagination works for each category: the first page is the base URL, and subsequent pages append /page/2/, /page/3/, etc.
* The categories you want to scrape are listed in the HTML `<select>`: AAR, All Judgements, High Court, Others, Supreme Court, Tribunal.

### Fetching Category Pages

* For each category, you can increment the page number in the URL until you receive a 404 error, indicating there are no more pages.

### Category Response Structure

* The sample in [category_response_sample.md](category_response_sample.md) shows that each category page contains several posts, each with a "read more" link.

### Read More Response

* The [readmore_response.md](readmore_response.md) file contains the HTML response you get when you follow a "read more" link for a post.
* You want to analyze this response to extract all possible information from each post, without missing any details.

### Goal

* The aim is to systematically fetch all posts for each category and page, follow their "read more" links, and extract as much information as possible from the detailed post pages.

### 1. Project Structure

shunyatax/
|
|
|--- main.py                # Orchestrates the scraping workflow
|--- config.py              # Stores categories, base URLs, and constants
|--- fetcher.py             # Handles HTTP requests and saving raw responses
|--- utils.py               # Helper functions (e.g., unique ID generation, file ops)
|--- requirements.txt       # Dependencies (requests, beautifulsoup4, etc.)
|--- ledger.csv             # Tracks unique_id, file path, and post URL
|--- progress_tracker.csv   # Tracks last fetched page for each category
|--- error_log.txt          # Logs persistent fetch errors
|--- <Category Folders>/    # e.g., AAR/, All_Judgements/, etc.
|    |
|    |--- page_N/
|    |    |
|    |    |--- category_response.html
|    |    |--- <unique_id>.html
|    |    |--- ...
|    |
|--- ...

### 2. Workflow

#### Configuration

List all categories and their base URLs in config.py.

#### Fetching & Saving

For each category and page:

1. Fetch the category page, save as category_response.html.
2. For each post:
    1. Generate a unique ID.
    2. Fetch the "read more" page, save as <unique_id>.html.
    3. Record unique ID, file path, and URL in ledger.csv.
3. After each page, update progress_tracker.csv with the latest page number for the category.

#### Rate Limiting

After processing each page, pause for a random interval between 2 and 8 seconds to avoid overloading the server:

```python
import random, time
time.sleep(random.uniform(2, 8))
```

#### Error Handling

- Wrap all network requests in try...except blocks.
- On failure, retry a few times with exponential backoff.
- If still unsuccessful, log the error and URL in error_log.txt for later review.
- On restart, use progress_tracker.csv to resume from the last successful page for each category.

#### Principles

1. Functions are small and focused.
2. Using plain CSV for the ledger and progress tracking.
3. No parsing or processing HTML at this stage—just saving raw responses for now.
4. Robust error handling and polite scraping practices.

## Project Phases

### Phase 1: Data Collection
- Scrape and save all category (listing) pages as `category_response.html` for each page of each category.
- For each post/judgement listed, follow the "Read More" link and save the full detail page as `<unique_id>.html`.
- Ensure all pages are downloaded and saved in the correct folder structure for each category and page.
- Track progress, errors, and missing files using CSV ledgers and logs.

### Phase 2: Data Extraction and Cleaning
- Extract all possible fields from both the category (summary) and readmore (detail) HTML files for each case.
- **Guidelines for Combining Data:**
    - **Always prefer the longer/more detailed value** for each field (title, summary, etc.).
    - **If a field is missing in the readmore/detail page, fall back to the category/summary page.**
    - **If a field is present in both, but the readmore version is longer, use the readmore version.**
    - **If a field is present in both but the content is different (not just length), prefer the more detailed/context-rich version (usually from the readmore page). Optionally, keep both for review or flag for manual inspection.**
    - **If the readmore page is missing a summary, use the category page's summary.**
    - **For dates, author, court, etc.:**
        - Extract from both; if missing in readmore, use category value; if both present, prefer the more detailed/complete value.
    - **Full text/body:**
        - Only available in the readmore page. Always use this.
    - **Related Judgements:**
        - If present in the readmore page, extract all related judgements (title, link, summary). If not present, leave blank or as an empty list.
- Store the result as a unified record for each case for later cleaning and ML training.

## Fields Present in Each Post Entry (Consistent Across Pages)

- **Title**
  - Example: "Tata Communications Ltd vs. UOI (Bombay High Court)"
  - Found in: `<h2 class="entry-title post-title"><a ...>TITLE</a></h2>`
- **Post URL**
  - Example: `https://itatonline.org/archives/tata-communications-ltd-vs-uoi-bombay-high-court-s-245-adjustment-of-refund...`
  - Found in: The `<a>` tag inside the title.
- **Date(s)**
  - **Date of Pronouncement**: e.g., "April 6, 2021"
  - **Date of Publication**: e.g., "April 24, 2021"
  - Found in: `<tr><td>DATE:</td><td>DATE (Date of pronouncement)</td></tr>` and `<tr><td>DATE:</td><td>DATE (Date of publication)</td></tr>`
- **Author**
  - Example: "editor"
  - Found in: `<span class="author vcard"><a ...>AUTHOR</a></span>`
- **Court**
  - Example: "Bombay High Court"
  - Found in: `<tr><td>COURT:</td><td>...</td></tr>`
- **Coram (Judges)**
  - Example: "Abhay Ahuja J, Sunil P. Deshmukh J"
  - Found in: `<tr><td>CORAM:</td><td>...</td></tr>`
- **Section(s)**
  - Example: "245", "147, 148"
  - Found in: `<tr><td>SECTION(S):</td><td>...</td></tr>`
- **Genre**
  - Example: "Domestic Tax", "Transfer Pricing"
  - Found in: `<tr><td>GENRE:</td><td>...</td></tr>`
- **Catch Words**
  - Example: "refund, stay of demand"
  - Found in: `<tr><td>CATCH WORDS:</td><td>...</td></tr>`
- **Counsel**
  - Example: "Atul Jasani, Harsh Kapadia, J.D. Mistri, Suresh Kumar"
  - Found in: `<tr><td>COUNSEL:</td><td>...</td></tr>`
- **AY (Assessment Year)**
  - Example: "AY 2019-20", "2012-13"
  - Found in: `<tr><td>AY:</td><td>...</td></tr>`
- **File Link**
  - Example: "Click here to view full post with file download link"
  - Found in: `<tr><td>FILE:</td><td> <a ...>Click here...</a> </td></tr>`
- **Citation**
  - Sometimes present, sometimes empty.
  - Found in: `<tr><td>CITATION:</td><td>...</td></tr>`
- **Summary/Extract**
  - A `<strong>` block or `<p>` after the table, summarizing the judgement.
- **Read More Link**
  - Example: `<div class="read-more"><a href="...">Read more ›</a></div>`

### Distribution and Consistency
- All these fields are present in the same structure across the first three and last three pages.
- Some fields (like Citation, Genre, AY) may be empty for certain posts, but the field itself is always present.
- The structure is highly consistent, making it possible to extract these fields reliably for each post.
- The "Read More" link always points to the full detail page for the judgement.

### Summary
The fields listed above are consistently available for each post across the sampled pages, with only occasional missing values (not missing fields). This structure should allow for robust extraction and unification into a dataset.

## Comments and Similar/Related Judgements Sections (Readmore/Detail Pages)

### Comments Section
- **Type:**
  - Most pages contain a 'Recent Comments' widget, which lists recent comments across the site, not specific to the current judgement.
  - Structure: `<div id="recent-comments-2" class="widget-wrapper widget_recent_comments">` containing a `<ul id="recentcomments">` with `<li class="recentcomments">` items.
  - Each comment includes:
    - **Comment Author** (sometimes with a link)
    - **Target Judgement** (as a link to the relevant judgement)
    - **Comment Text** (sometimes visible, sometimes just a reference)
- **Case-Specific Comments:**
  - No evidence of case-specific comment threads or forms in the sampled files, but the presence of comment-related CSS and RSS links suggests some templates may support it.
- **Extraction Note:**
  - For most cases, only global recent comments are available. If case-specific comments are found in other files, extract all available details (author, text, date, etc.).

### Similar/Related Judgements Section
- **Type:**
  - Some readmore/detail pages contain a 'Related Judgements' or 'Similar Judgements' section.
  - Structure: Typically a heading like `<h2 align="center">Related Judgements</h2>` followed by an ordered list `<ol>` of related cases.
  - Each related case includes:
    - **Title** (linked to the related judgement)
    - **Short summary or excerpt**
- **Extraction Note:**
  - If present, extract all related judgements (title, link, summary) for each case. If not present, leave blank or as an empty list.

### Summary
- The presence of these sections is not guaranteed for every case. Always check for their existence and extract all available details when present.
- For robust extraction, search for widgets, headings, or sections with keywords like 'comment', 'related', or 'similar' in the class, id, or heading text.
