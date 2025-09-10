import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Firecrawl API ---
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# --- File Paths ---
BLOCKED_DOMAINS_PATH = "filters/blocked_domains.json"
TRUSTED_SOURCES_PATH = "filters/trusted_sources.json"

# --- Search Parameters ---
SEARCH_DOMAINS = [
    "*.ai",
    "*.io",
    "*.org",
    "*.edu",
    "*.com",
    "*.co",
    "*.net",
    "*.tech",
    "*.news",
    "*.media"
]

# --- Parsing Parameters ---
MIN_CONTENT_LENGTH = 10000  # Minimum number of characters for a valid article
CONCURRENT_REQUESTS = 5   # Number of concurrent requests to Firecrawl Scrape API

# --- Scoring Weights ---
TRUST_SCORE_WEIGHT = 0.5
RELEVANCE_SCORE_WEIGHT = 0.3
DEPTH_SCORE_WEIGHT = 0.2

# --- Selection ---
TOP_N_SOURCES = 5
