import asyncio
import sys
import os
import json
import re
import argparse
from src.logger_config import logger
from src.firecrawl_client import FirecrawlClient
from src.processing import (
    filter_urls,
    validate_and_prepare_sources,
    score_sources,
    select_best_sources,
    clean_content,
)
from src.llm_processing import (
    extract_prompts_from_article,
    generate_wordpress_article,
)
from src.token_tracker import TokenTracker
from src.config import LLM_MODELS

def sanitize_filename(topic):
    """Sanitizes the topic to be used as a valid directory name."""
    return re.sub(r'[\\/*?:"<>|]', "_", topic).replace(" ", "_")

def save_artifact(data, path, filename):
    """Saves data to a file (JSON or text)."""
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=4, ensure_ascii=False)
    logger.info(f"Saved artifact to {filepath}")

async def main_flow(topic: str, model_overrides: dict = None):
    """
The main pipeline for WordPress article generation.
    
    Args:
        topic: The topic for content generation
        model_overrides: Dictionary to override default models for specific stages
    """
    logger.info(f"--- Starting Content Generation Pipeline for topic: '{topic}' ---")
    
    # Initialize token tracker
    token_tracker = TokenTracker(topic=topic)
    
    # Prepare model configuration with overrides
    model_overrides = model_overrides or {}
    from src.config import LLM_MODELS
    active_models = {**LLM_MODELS, **model_overrides}
    
    if model_overrides:
        logger.info(f"Using model overrides: {model_overrides}")

    # --- Setup Directories ---
    sanitized_topic = sanitize_filename(topic)
    base_output_path = os.path.join("output", sanitized_topic)
    paths = {
        "search": os.path.join(base_output_path, "01_search"),
        "parsing": os.path.join(base_output_path, "02_parsing"),
        "scoring": os.path.join(base_output_path, "03_scoring"),
        "selection": os.path.join(base_output_path, "04_selection"),
        "cleaning": os.path.join(base_output_path, "05_cleaning"),
        "extraction": os.path.join(base_output_path, "06_extracted_prompts"),
        "final_article": os.path.join(base_output_path, "07_final_article"),
    }
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    # --- Этапы 1-6: Поиск и очистка ---
    firecrawl_client = FirecrawlClient()
    search_results = await firecrawl_client.search(topic)
    save_artifact(search_results, paths["search"], "01_search_results.json")
    
    urls = [result['url'] for result in search_results if 'url' in result]
    if not urls:
        logger.error("No URLs found in search results. Exiting.")
        return
    save_artifact(urls, paths["search"], "02_extracted_urls.json")

    clean_urls = filter_urls(urls)
    save_artifact(clean_urls, paths["parsing"], "01_clean_urls.json")
    
    if not clean_urls:
        logger.error("No clean URLs left after filtering. Exiting.")
        return

    scraped_data = await firecrawl_client.scrape_urls(clean_urls)
    save_artifact(scraped_data, paths["parsing"], "02_scraped_data.json")

    valid_sources = validate_and_prepare_sources(scraped_data)
    save_artifact(valid_sources, paths["parsing"], "03_valid_sources.json")

    if not valid_sources:
        logger.error("No valid sources found after scraping and validation. Exiting.")
        return

    scored_sources = score_sources(valid_sources, topic)
    save_artifact(scored_sources, paths["scoring"], "scored_sources.json")

    top_sources = select_best_sources(scored_sources)
    save_artifact(top_sources, paths["selection"], "top_5_sources.json")

    if not top_sources:
        logger.error("Could not select any top sources. Exiting.")
        return

    cleaned_sources = clean_content(top_sources)
    save_artifact(cleaned_sources, paths["cleaning"], "final_cleaned_sources.json")

    # Log cleaning metrics summary
    total_original = sum(source.get('original_length', 0) for source in cleaned_sources)
    total_cleaned = sum(source.get('cleaned_length', 0) for source in cleaned_sources)
    overall_reduction = ((total_original - total_cleaned) / total_original * 100) if total_original > 0 else 0
    logger.info(f"Content cleaning summary: {total_original:,} → {total_cleaned:,} chars ({overall_reduction:.1f}% reduction)")

    # --- Этап 7: Извлечение промптов ---
    all_prompts = []
    for i, source in enumerate(cleaned_sources):
        source_id = f"source_{i+1}"
        prompts = extract_prompts_from_article(
            article_text=source['cleaned_content'], 
            topic=topic, 
            base_path=paths["extraction"],
            source_id=source_id,
            token_tracker=token_tracker,
            model_name=active_models.get("extract_prompts")
        )
        all_prompts.extend(prompts)
    save_artifact(all_prompts, paths["extraction"], "all_prompts.json")
    
    if not all_prompts:
        logger.error("No prompts could be extracted from the sources. Exiting.")
        return

    # --- New Stage: Generate WordPress Article ---
    logger.info("Generating WordPress-ready article from collected prompts...")
    wordpress_data = generate_wordpress_article(
        prompts=all_prompts, 
        topic=topic, 
        base_path=paths["final_article"],
        token_tracker=token_tracker,
        model_name=active_models.get("generate_article")
    )
    
    # Сохраняем полную JSON структуру
    save_artifact(wordpress_data, paths["final_article"], "wordpress_data.json")
    
    # Сохраняем отдельно HTML контент для удобства
    if isinstance(wordpress_data, dict) and "content" in wordpress_data:
        save_artifact(wordpress_data["content"], paths["final_article"], "article_content.html")
        logger.info(f"Generated article: {wordpress_data.get('title', 'No title')}")
    else:
        logger.error("Invalid WordPress data structure returned")

    # --- Save Token Usage Report ---
    token_report_path = token_tracker.save_token_report(
        base_path=base_output_path,
        filename="token_usage_report.json"
    )
    
    logger.info("--- Pipeline Finished ---")
    logger.info(f"All artifacts saved in: {base_output_path}")
    if token_report_path:
        logger.info(f"Token usage report: {token_report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Content Generation Pipeline for WordPress")
    parser.add_argument("topic", type=str, help="The topic for content generation.")
    parser.add_argument("--extract-model", type=str, help="Model for prompt extraction (overrides config)")
    parser.add_argument("--generate-model", type=str, help="Model for article generation (overrides config)")
    parser.add_argument("--provider", type=str, choices=["deepseek", "openrouter"], 
                       help="LLM provider (deepseek or openrouter)")
    args = parser.parse_args()

    # Override config with command line arguments
    override_models = {}
    if args.extract_model:
        override_models["extract_prompts"] = args.extract_model
    if args.generate_model:
        override_models["generate_article"] = args.generate_model

    asyncio.run(main_flow(args.topic, model_overrides=override_models))