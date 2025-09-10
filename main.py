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
    rank_and_select_prompts,
    generate_expert_content_for_prompt,
    assemble_final_article,
)

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

async def main_flow(topic: str, stage: int):
    """
The main pipeline, stoppable at different stages.
    """
    logger.info(f"--- Starting Content Generation Pipeline for topic: '{topic}' (up to stage {stage}) ---")

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
        "ranking": os.path.join(base_output_path, "07_ranked_prompts"),
        "enrichment": os.path.join(base_output_path, "08_enriched_prompts"),
        "final_article": os.path.join(base_output_path, "09_final_article"),
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

    # --- Этап 7: Извлечение промптов ---
    all_prompts = []
    for i, source in enumerate(cleaned_sources):
        source_id = f"source_{i+1}"
        prompts = extract_prompts_from_article(
            article_text=source['cleaned_content'], 
            topic=topic, 
            base_path=paths["extraction"],
            source_id=source_id
        )
        all_prompts.extend(prompts)
    save_artifact(all_prompts, paths["extraction"], "all_prompts.json")
    
    if stage == 7:
        logger.info(f"--- Pipeline stopped after stage 7 as requested. ---")
        return

    if not all_prompts:
        logger.error("No prompts could be extracted from the sources. Exiting.")
        return

    # --- Этап 8: Ранжирование и отбор ---
    best_prompts = rank_and_select_prompts(
        prompts=all_prompts, 
        topic=topic, 
        base_path=paths["ranking"]
    )
    save_artifact(best_prompts, paths["ranking"], "best_prompts.json")

    if stage == 8:
        logger.info(f"--- Pipeline stopped after stage 8 as requested. ---")
        return

    if not best_prompts:
        logger.error("LLM failed to rank or select any prompts. Exiting.")
        return

    # --- Этап 9: Обогащение контента ---
    enriched_prompts = []
    for i, prompt in enumerate(best_prompts):
        # Pass the whole prompt object for context
        enriched_prompt = generate_expert_content_for_prompt(
            prompt=prompt, 
            base_path=paths["enrichment"],
            prompt_index=i+1
        )
        enriched_prompts.append(enriched_prompt)
    save_artifact(enriched_prompts, paths["enrichment"], "enriched_prompts.json")

    if stage == 9:
        logger.info(f"--- Pipeline stopped after stage 9 as requested. ---")
        return

    # --- Этап 10: Сборка статьи ---
    final_article_md = assemble_final_article(
        enriched_prompts=enriched_prompts, 
        topic=topic, 
        base_path=paths["final_article"]
    )
    save_artifact(final_article_md, paths["final_article"], "final_article.md")

    logger.info("--- Pipeline Finished ---")
    logger.info(f"All artifacts saved in: {base_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Content Generation Pipeline")
    parser.add_argument("topic", type=str, help="The topic for content generation.")
    parser.add_argument("--stage", type=int, default=10, help="Stage to run up to (7, 8, 9, or 10). Default is 10 (full run).")
    args = parser.parse_args()

    asyncio.run(main_flow(args.topic, args.stage))