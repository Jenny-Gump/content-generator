import json
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

from src.config import (
    BLOCKED_DOMAINS_PATH,
    TRUSTED_SOURCES_PATH,
    MIN_CONTENT_LENGTH,
    TRUST_SCORE_WEIGHT,
    RELEVANCE_SCORE_WEIGHT,
    DEPTH_SCORE_WEIGHT,
    TOP_N_SOURCES,
)
from src.logger_config import logger

def _load_json_file(file_path: str) -> Dict:
    """Loads a JSON file and returns its content."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}")
        return {}

def filter_urls(urls: List[str]) -> List[str]:
    """
    Filters URLs based on a blocklist of domains and URL patterns.
    """
    logger.info(f"Starting URL filtering for {len(urls)} URLs.")
    blocklist = _load_json_file(BLOCKED_DOMAINS_PATH)
    blocked_domains = set(blocklist.get("domains", []))
    blocked_patterns = blocklist.get("patterns", [])

    clean_urls = []
    for url in urls:
        try:
            domain = urlparse(url).netloc
            if domain in blocked_domains:
                logger.warning(f"Blocking URL from domain: {url}")
                continue
            
            if any(pattern in url for pattern in blocked_patterns):
                logger.warning(f"Blocking URL with pattern: {url}")
                continue
            
            clean_urls.append(url)
        except Exception as e:
            logger.error(f"Could not parse URL {url}: {e}")
            continue
            
    logger.info(f"Finished URL filtering. {len(clean_urls)} URLs remaining.")
    return clean_urls

def validate_and_prepare_sources(scraped_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates scraped articles based on minimum length and prepares the data structure.
    """
    logger.info(f"Validating {len(scraped_data)} scraped articles.")
    valid_sources = []
    for data in scraped_data:
        content = data.get('markdown', '')
        metadata = data.get('metadata', {})
        url = metadata.get('sourceURL')

        if len(content) >= MIN_CONTENT_LENGTH:
            source = {
                "url": url,
                "title": metadata.get('title'),
                "content": content
            }
            valid_sources.append(source)
        else:
            logger.warning(f"Discarding source {url} due to short content length ({len(content)} characters).")
    
    logger.info(f"{len(valid_sources)} sources passed validation.")
    return valid_sources

def score_sources(sources: List[Dict[str, Any]], topic: str) -> List[Dict[str, Any]]:
    """
    Scores each source based on trust, relevance, and depth.
    """
    logger.info(f"Scoring {len(sources)} sources.")
    trusted_sources = _load_json_file(TRUSTED_SOURCES_PATH)
    keywords = set(topic.lower().split())

    for source in sources:
        if not source.get('url') or not source.get('title'):
            source['trust_score'] = 0
            source['relevance_score'] = 0
            source['depth_score'] = 0
            continue

        # 1. Trust Score
        domain = urlparse(source["url"]).netloc
        source["trust_score"] = trusted_sources.get(domain, 1.0)

        # 2. Relevance Score
        title_matches = sum(1 for word in keywords if word in source["title"].lower())
        content_matches = sum(1 for word in keywords if word in source["content"].lower())
        source["relevance_score"] = (title_matches * 3) + content_matches

        # 3. Depth Score
        source["depth_score"] = len(source["content"])

    logger.info("Finished scoring sources.")
    return sources

def select_best_sources(scored_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Selects the top N sources based on a weighted final score.
    """
    if not scored_sources:
        return []
        
    logger.info("Selecting the best sources.")
    max_relevance = max((s.get("relevance_score", 0) for s in scored_sources), default=1) or 1
    max_depth = max((s.get("depth_score", 0) for s in scored_sources), default=1) or 1

    for source in scored_sources:
        source["normalized_relevance"] = source.get("relevance_score", 0) / max_relevance
        source["normalized_depth"] = source.get("depth_score", 0) / max_depth

        source["final_score"] = (
            source.get("trust_score", 0) * TRUST_SCORE_WEIGHT +
            source["normalized_relevance"] * RELEVANCE_SCORE_WEIGHT +
            source["normalized_depth"] * DEPTH_SCORE_WEIGHT
        )

    sorted_sources = sorted(scored_sources, key=lambda x: x.get("final_score", 0), reverse=True)
    top_sources = sorted_sources[:TOP_N_SOURCES]
    
    logger.info(f"Selected top {len(top_sources)} sources.")
    for i, source in enumerate(top_sources):
        logger.info(f"  {i+1}. {source.get('url', 'N/A')} (Score: {source.get('final_score', 0):.2f})")
        
    return top_sources

def clean_content(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans the Markdown content of the top sources with improved regex patterns.
    """
    logger.info(f"Cleaning content for {len(sources)} sources.")
    
    for source in sources:
        text = source.get("content", "")

        # Pattern to remove markdown links but keep the text, e.g., [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Pattern to remove image links, e.g., ![alt](url)
        text = re.sub(r'!\\\[[^\\]*\]\([^)]+\)', '', text)

        # Pattern to remove bare URLs in parentheses
        text = re.sub(r'\(\s*https?://[^)]+\)', '', text)

        # Remove common UI words/phrases
        text = re.sub(r'\b(Share|Watch Now|Mark as Completed|Table of Contents|Contents|Menu|Search|Log in|Sign up|Back to top|Read more)\b', '', text, flags=re.IGNORECASE)

        # Remove lines that are just markdown separators or noise
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            stripped_line = line.strip()
            # Keep the line if it's not empty and doesn't consist solely of markdown separators
            if stripped_line and not re.fullmatch(r'[\s\*\-_#>=]+', stripped_line):
                clean_lines.append(stripped_line)
        
        # Rejoin and clean up excessive newlines
        cleaned_text = '\n'.join(clean_lines)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        source["cleaned_content"] = cleaned_text.strip()
        
    logger.info("Finished cleaning content.")
    return sources