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

# --- WordPress Publishing Configuration ---
WORDPRESS_API_URL = os.getenv("WORDPRESS_API_URL", "https://ailynx.ru/wp-json/wp/v2")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME", "PetrovA")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")
USE_CUSTOM_META_ENDPOINT = os.getenv("USE_CUSTOM_META_ENDPOINT", "true").lower() == "true"
CUSTOM_POST_META_API_KEY = os.getenv("CUSTOM_POST_META_API_KEY", "")
WORDPRESS_CATEGORY = os.getenv("WORDPRESS_CATEGORY", "prompts")
WORDPRESS_STATUS = os.getenv("WORDPRESS_STATUS", "draft")

# --- LLM Models Configuration ---
# Models for different pipeline stages
LLM_MODELS = {
    "extract_prompts": "google/gemini-2.5-flash-lite-preview-06-17",      # Model for prompt extraction from articles
    "generate_article": "deepseek-reasoner",                             # Model for WordPress article generation (switched from gemini)
    "editorial_review": "google/gemini-2.5-flash-lite-preview-06-17",    # Model for editorial review and cleanup (switched from deepseek)
}

# Default model if no specific model is configured
DEFAULT_MODEL = "deepseek-reasoner"

# --- LLM Providers Configuration ---
LLM_PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "models": [
            "deepseek-reasoner", 
            "deepseek-chat"
        ]
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY", 
        "models": [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "google/gemini-2.0-flash-001",
            "google/gemini-2.5-flash-lite-preview-06-17"
        ],
        "extra_headers": {
            "HTTP-Referer": "https://github.com/your-repo/content-generator",
            "X-Title": "AI Content Generator"
        }
    }
}

# Model to provider mapping
def get_provider_for_model(model_name: str) -> str:
    """Get the provider name for a given model."""
    for provider, config in LLM_PROVIDERS.items():
        if model_name in config["models"]:
            return provider
    # Default to deepseek for unknown models
    return "deepseek"
