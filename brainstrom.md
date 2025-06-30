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
