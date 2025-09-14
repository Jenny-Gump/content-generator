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
    editorial_review,
)
from src.wordpress_publisher import WordPressPublisher
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

async def basic_articles_flow(topic: str, model_overrides: dict = None, publish_to_wordpress: bool = True):
    """
    Pipeline for generating basic articles with FAQ and sources.

    Args:
        topic: The topic for content generation
        model_overrides: Dictionary to override default models for specific stages
        publish_to_wordpress: Whether to publish to WordPress
    """
    logger.info(f"--- Starting Basic Articles Pipeline for topic: '{topic}' ---")

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
        "structure_extraction": os.path.join(base_output_path, "06_structure_extraction"),
        "ultimate_structure": os.path.join(base_output_path, "07_ultimate_structure"),
        "final_article": os.path.join(base_output_path, "08_final_article"),
        "editorial_review": os.path.join(base_output_path, "09_editorial_review"),
    }
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    # --- Этапы 1-6: Поиск, парсинг, очистка (те же что в main_flow) ---
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

    # --- Этап 7: Извлечение структур (вместо промптов) ---
    logger.info(f"Starting structure extraction from {len(cleaned_sources)} sources...")
    all_structures = []
    extraction_stats = []

    for i, source in enumerate(cleaned_sources):
        source_id = f"source_{i+1}"
        logger.info(f"Extracting structure from {source_id}...")

        structures = extract_prompts_from_article(
            article_text=source['cleaned_content'],
            topic=topic,
            base_path=paths["structure_extraction"],
            source_id=source_id,
            token_tracker=token_tracker,
            model_name=active_models.get("extract_prompts"),
            content_type="basic_articles"  # Используем папку basic_articles
        )

        extraction_stats.append({
            "source_id": source_id,
            "url": source.get('url', 'Unknown'),
            "structures_extracted": len(structures)
        })

        if len(structures) == 0:
            logger.warning(f"⚠️  {source_id} extracted 0 structures - possible JSON parsing issue")
        else:
            logger.info(f"✅ {source_id} extracted {len(structures)} structures")

        all_structures.extend(structures)

    save_artifact(all_structures, paths["structure_extraction"], "all_structures.json")

    if not all_structures:
        logger.error("No structures could be extracted from the sources. Exiting.")
        return

    # --- Этап 8: Создание ультимативной структуры ---
    logger.info("Creating ultimate structure from extracted structures...")

    # Используем специальный промпт для создания ультимативной структуры
    from src.llm_processing import _load_and_prepare_messages, _make_llm_request_with_retry, save_llm_interaction

    messages = _load_and_prepare_messages(
        "basic_articles",
        "02_create_ultimate_structure",
        {"topic": topic, "article_text": json.dumps(all_structures, indent=2)}
    )

    response_obj, actual_model = _make_llm_request_with_retry(
        stage_name="create_structure",
        model_name=active_models.get("create_structure"),
        messages=messages,
        token_tracker=token_tracker,
        temperature=0.3
    )

    content = response_obj.choices[0].message.content
    save_llm_interaction(
        base_path=paths["ultimate_structure"],
        stage_name="create_structure",
        messages=messages,
        response=content,
        request_id="ultimate_structure"
    )

    # Парсим ответ
    from src.llm_processing import _parse_json_from_response
    ultimate_structure = _parse_json_from_response(content)

    save_artifact(ultimate_structure, paths["ultimate_structure"], "ultimate_structure.json")

    if not ultimate_structure:
        logger.error("Could not create ultimate structure. Exiting.")
        return

    # --- Этап 9: Генерация WordPress статьи ---
    logger.info("Generating WordPress-ready article from ultimate structure...")
    wordpress_data = generate_wordpress_article(
        prompts=ultimate_structure,
        topic=topic,
        base_path=paths["final_article"],
        token_tracker=token_tracker,
        model_name=active_models.get("generate_article"),
        content_type="basic_articles"
    )

    save_artifact(wordpress_data, paths["final_article"], "wordpress_data.json")

    if isinstance(wordpress_data, dict) and "content" in wordpress_data:
        save_artifact(wordpress_data["content"], paths["final_article"], "article_content.html")
        logger.info(f"Generated article: {wordpress_data.get('title', 'No title')}")
    else:
        logger.error("Invalid WordPress data structure returned")

    # --- Этап 10: Editorial Review ---
    logger.info("Starting editorial review and cleanup...")
    raw_response = wordpress_data.get("raw_response", "")
    wordpress_data_final = editorial_review(
        raw_response=raw_response,
        topic=topic,
        base_path=paths["editorial_review"],
        token_tracker=token_tracker,
        model_name=active_models.get("editorial_review"),
        content_type="basic_articles"
    )

    save_artifact(wordpress_data_final, paths["editorial_review"], "wordpress_data_final.json")

    if isinstance(wordpress_data_final, dict) and "content" in wordpress_data_final:
        save_artifact(wordpress_data_final["content"], paths["editorial_review"], "article_content_final.html")
        logger.info(f"Editorial review completed: {wordpress_data_final.get('title', 'No title')}")
    else:
        logger.warning("Editorial review returned invalid structure, using original data")
        wordpress_data_final = wordpress_data

    # --- Этап 11: WordPress Publication (опционально) ---
    if publish_to_wordpress:
        logger.info("--- Starting WordPress Publication ---")
        try:
            wp_publisher = WordPressPublisher()

            # Test connection first
            logger.info("Testing WordPress connection...")
            from src.wordpress_publisher import test_wordpress_connection
            if test_wordpress_connection():
                logger.info("✅ WordPress connection successful")

                # Publish article (use final edited version)
                publication_result = wp_publisher.publish_article(wordpress_data_final)

                # Save publication results
                save_artifact(publication_result, paths["editorial_review"], "wordpress_publication_result.json")

                if publication_result['success']:
                    logger.info(f"🎉 Article successfully published to WordPress!")
                    logger.info(f"📝 WordPress ID: {publication_result['wordpress_id']}")
                    logger.info(f"🔗 Edit URL: {publication_result['url']}")
                else:
                    logger.error(f"❌ WordPress publication failed: {publication_result['error']}")
            else:
                logger.error("❌ WordPress connection test failed, skipping publication")

        except Exception as e:
            logger.error(f"❌ WordPress publication error: {str(e)}")
            save_artifact({
                'success': False,
                'error': str(e)
            }, paths["editorial_review"], "wordpress_publication_result.json")
    else:
        logger.info("📝 WordPress publication skipped (use --publish-wp to enable)")

    # --- Save Token Usage Report ---
    token_report_path = token_tracker.save_token_report(
        base_path=base_output_path,
        filename="token_usage_report.json"
    )

    logger.info("--- Basic Articles Pipeline Finished ---")
    logger.info(f"All artifacts saved in: {base_output_path}")
    if token_report_path:
        logger.info(f"Token usage report: {token_report_path}")


async def main_flow(topic: str, model_overrides: dict = None, publish_to_wordpress: bool = True, content_type: str = "prompt_collection"):
    """
The main pipeline for WordPress article generation.

    Args:
        topic: The topic for content generation
        model_overrides: Dictionary to override default models for specific stages
        publish_to_wordpress: Whether to publish to WordPress
        content_type: Content type (prompt_collection, basic_articles)
    """
    logger.info(f"--- Starting Content Generation Pipeline for topic: '{topic}' ---")
    logger.info(f"--- Content Type: {content_type} ---")
    
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
        "editorial_review": os.path.join(base_output_path, "08_editorial_review"),
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
    logger.info(f"Starting prompt extraction from {len(cleaned_sources)} sources...")
    all_prompts = []
    extraction_stats = []
    
    for i, source in enumerate(cleaned_sources):
        source_id = f"source_{i+1}"
        logger.info(f"Extracting prompts from {source_id}...")
        
        prompts = extract_prompts_from_article(
            article_text=source['cleaned_content'], 
            topic=topic, 
            base_path=paths["extraction"],
            source_id=source_id,
            token_tracker=token_tracker,
            model_name=active_models.get("extract_prompts")
        )
        
        extraction_stats.append({
            "source_id": source_id,
            "url": source.get('url', 'Unknown'),
            "prompts_extracted": len(prompts)
        })
        
        if len(prompts) == 0:
            logger.warning(f"⚠️  {source_id} extracted 0 prompts - possible JSON parsing issue")
        else:
            logger.info(f"✅ {source_id} extracted {len(prompts)} prompts")
            
        all_prompts.extend(prompts)
    
    # Extraction summary
    total_expected = len(cleaned_sources) * 2  # Expected 2 prompts per source
    total_extracted = len(all_prompts)
    success_rate = (total_extracted / total_expected * 100) if total_expected > 0 else 0
    
    logger.info(f"🔍 Prompt extraction summary:")
    logger.info(f"   Sources processed: {len(cleaned_sources)}")
    logger.info(f"   Prompts extracted: {total_extracted}/{total_expected} ({success_rate:.1f}% success rate)")
    
    # Detailed breakdown
    for stat in extraction_stats:
        logger.info(f"   {stat['source_id']}: {stat['prompts_extracted']} prompts")
    
    # Validation warnings
    if total_extracted < (total_expected * 0.8):  # Less than 80% success rate
        logger.warning(f"⚠️  Low extraction success rate ({success_rate:.1f}%). Consider checking for JSON parsing issues.")
    
    save_artifact(all_prompts, paths["extraction"], "all_prompts.json")
    
    if not all_prompts:
        logger.error("No prompts could be extracted from the sources. Exiting.")
        return

    # --- Этап 7: Generate WordPress Article ---
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
        
    # --- Этап 8: Editorial Review ---
    logger.info("Starting editorial review and cleanup...")
    raw_response = wordpress_data.get("raw_response", "")
    wordpress_data_final = editorial_review(
        raw_response=raw_response,
        topic=topic,
        base_path=paths["editorial_review"],
        token_tracker=token_tracker,
        model_name=active_models.get("editorial_review")
    )
    
    # Сохраняем отредактированную статью
    save_artifact(wordpress_data_final, paths["editorial_review"], "wordpress_data_final.json")
    
    # Сохраняем отдельно финальный HTML контент
    if isinstance(wordpress_data_final, dict) and "content" in wordpress_data_final:
        save_artifact(wordpress_data_final["content"], paths["editorial_review"], "article_content_final.html")
        logger.info(f"Editorial review completed: {wordpress_data_final.get('title', 'No title')}")
    else:
        logger.warning("Editorial review returned invalid structure, using original data")
        wordpress_data_final = wordpress_data

    # --- Этап 9: WordPress Publication (опционально) ---
    if publish_to_wordpress:
        logger.info("--- Starting WordPress Publication ---")
        try:
            wp_publisher = WordPressPublisher()
            
            # Test connection first
            logger.info("Testing WordPress connection...")
            from src.wordpress_publisher import test_wordpress_connection
            if test_wordpress_connection():
                logger.info("✅ WordPress connection successful")
                
                # Publish article (use final edited version)
                publication_result = wp_publisher.publish_article(wordpress_data_final)
                
                # Save publication results
                save_artifact(publication_result, paths["editorial_review"], "wordpress_publication_result.json")
                
                if publication_result['success']:
                    logger.info(f"🎉 Article successfully published to WordPress!")
                    logger.info(f"📝 WordPress ID: {publication_result['wordpress_id']}")
                    logger.info(f"🔗 Edit URL: {publication_result['url']}")
                else:
                    logger.error(f"❌ WordPress publication failed: {publication_result['error']}")
            else:
                logger.error("❌ WordPress connection test failed, skipping publication")
                
        except Exception as e:
            logger.error(f"❌ WordPress publication error: {str(e)}")
            save_artifact({
                'success': False, 
                'error': str(e)
            }, paths["editorial_review"], "wordpress_publication_result.json")
    else:
        logger.info("📝 WordPress publication skipped (use --publish-wp to enable)")

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
    
    # Основные аргументы
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("topic", type=str, nargs="?", help="The topic for content generation (single mode)")
    group.add_argument("--batch", type=str, help="Path to file with topics for batch processing")
    
    # Модели
    parser.add_argument("--extract-model", type=str, help="Model for prompt extraction (overrides config)")
    parser.add_argument("--generate-model", type=str, help="Model for article generation (overrides config)")
    parser.add_argument("--editorial-model", type=str, help="Model for editorial review and cleanup (overrides config)")
    parser.add_argument("--provider", type=str, choices=["deepseek", "openrouter"], 
                       help="LLM provider (deepseek or openrouter)")
    
    # Настройки публикации
    parser.add_argument("--no-publish", action="store_true", 
                       help="Skip WordPress publication (by default articles are published)")
    
    # Настройки батч-обработки
    parser.add_argument("--content-type", type=str, default="prompt_collection",
                       help="Content type for batch processing (default: prompt_collection)")
    parser.add_argument("--resume", action="store_true", 
                       help="Resume previous batch processing session")
    
    args = parser.parse_args()

    # Валидация аргументов
    if not args.topic and not args.batch:
        parser.error("Either topic or --batch must be specified")

    # Override config with command line arguments
    override_models = {}
    if args.extract_model:
        override_models["extract_prompts"] = args.extract_model
    if args.generate_model:
        override_models["generate_article"] = args.generate_model
    if args.editorial_model:
        override_models["editorial_review"] = args.editorial_model

    # By default publish to WordPress, unless --no-publish is specified
    publish_to_wp = not args.no_publish

    # Запуск в зависимости от режима
    if args.batch:
        # Режим батч-обработки
        logger.info(f"🎯 Starting batch processing mode")
        logger.info(f"   Topics file: {args.batch}")
        logger.info(f"   Content type: {args.content_type}")
        logger.info(f"   Resume: {args.resume}")
        logger.info(f"   Publish to WordPress: {publish_to_wp}")
        
        from batch_processor import run_batch_processor
        
        try:
            success = asyncio.run(run_batch_processor(
                topics_file=args.batch,
                content_type=args.content_type,
                model_overrides=override_models if override_models else None,
                resume=args.resume,
                skip_publication=not publish_to_wp
            ))
            
            if success:
                logger.info("✅ Batch processing completed successfully")
            else:
                logger.error("❌ Batch processing completed with errors")
                sys.exit(1)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Batch processing interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.error(f"💥 Batch processing failed: {e}")
            sys.exit(1)
    else:
        # Обычный одиночный режим
        logger.info(f"📝 Starting single topic processing mode")
        logger.info(f"   Topic: {args.topic}")
        logger.info(f"   Publish to WordPress: {publish_to_wp}")
        

        # Выберем правильную функцию в зависимости от content_type
        if args.content_type == "basic_articles":
            asyncio.run(basic_articles_flow(args.topic, model_overrides=override_models, publish_to_wordpress=publish_to_wp))
        else:
            asyncio.run(main_flow(args.topic, model_overrides=override_models, publish_to_wordpress=publish_to_wp))