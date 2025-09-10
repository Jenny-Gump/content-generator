## Project: AI-Powered Content Generation Pipeline

This project automates the process of finding, scraping, evaluating, and cleaning web articles on a given topic to produce high-quality source material.

### How it Works

The pipeline executes a 6-step flow:
1.  **Request:** Takes a topic from the command line.
2.  **Search:** Performs a broad search using the Firecrawl API to get top web results.
3.  **Parse & Filter:** Scrapes the content from the URLs, filters them by a blocklist (`filters/blocked_domains.json`), and validates them by minimum content length.
4.  **Score:** Ranks the valid articles based on trust (from `filters/trusted_sources.json`), relevance to the topic, and content depth.
5.  **Select:** Selects the top 5 highest-scoring articles.
6.  **Clean:** Removes boilerplate, ads, and other noise from the final articles using advanced regex.

### How to Run

1.  **Activate virtual environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Run the main script with a topic:**
    ```bash
    python main.py "Your topic here"
    ```
3.  **Check the `output/` directory** for all generated artifacts and the final cleaned `.md` files.
