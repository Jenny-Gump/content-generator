# AI-Powered Content Generation Pipeline

This project is an automated pipeline for generating high-quality content based on a given topic. It leverages the Firecrawl API to search for relevant sources, scrapes their content, scores them based on a set of criteria, and cleans the best articles for final use.

## Latest Updates (September 2025)

### 🆓 **100% FREE MODELS + RELIABILITY SYSTEM** (NEW - September 13, 2025)
- **FREE DeepSeek Models**: All pipeline stages now use `deepseek/deepseek-chat-v3.1:free` by default via OpenRouter
- **Zero Token Costs**: Normal operations run completely free with automatic fallbacks to premium models only on failures
- **3-Level Retry System**: Automatic retries with exponential backoff (2s → 5s → 10s)
- **Smart Fallbacks**: Primary free models with premium fallbacks (Gemini 2.5, paid DeepSeek)
- **Enhanced Logging**: Detailed model usage tracking with retry attempt counts
- **Python 3.13 Compatible**: Fixed all SyntaxWarnings for latest Python versions
- **Streamlined Batch Processing**: Removed WordPress verification delays for faster processing

### 🎯 RGCSC Prompt Enhancement Framework (NEW!)
- **Intelligent Prompt Analysis**: LLM-1 теперь анализирует каждый найденный промпт по фреймворку RGCSC (Role-Goal-Context-Style-Constraints)
- **Автоматическое обогащение**: Неполные промпты автоматически дополняются недостающими элементами структуры
- **Профессиональное качество**: Простые промпты типа "Create video ideas" превращаются в полноценные структурированные промпты с ролями, контекстом и ограничениями
- **Готовые к использованию**: Все извлеченные промпты становятся self-contained и сразу применимыми
- **Обновленные критерии**: Добавлен "Structural Completeness" как первый критерий оценки промптов
- **Конкретные примеры**: Встроенные примеры показывают трансформацию "до" и "после" обогащения

### 🚀 WordPress Integration
- **Автоматическая публикация**: По умолчанию все статьи публикуются на https://ailynx.ru
- **Yoast SEO поддержка**: Автоматическое заполнение SEO полей (_yoast_wpseo_title, _yoast_wpseo_metadesc, focus_keyword)
- **Категория "prompts"**: Все статьи автоматически публикуются в специальной категории
- **Черновики по умолчанию**: Безопасная публикация в статусе draft для проверки
- **Флаг --no-publish**: Опциональное отключение публикации через командную строку
- **Полное тестирование**: Готовые скрипты для тестирования интеграции

### 🎯 Batch Processing System (NEW!)
- **Sequential Processing**: Process multiple topics from a text file, one by one
- **WordPress Verification**: Strict publication verification before moving to next topic
- **Memory Management**: Built-in memory monitoring and cleanup between topics
- **Resume Support**: Continue from where you left off with `--resume` flag
- **Content Types**: Modular system supporting different content types (prompts, business ideas, etc.)
- **Progress Tracking**: Detailed progress files and failed topic logging
- **Timeout Protection**: Per-topic timeouts and retry mechanisms
- **Graceful Shutdown**: Safe interruption with cleanup and progress saving

### 🎛️ Command Line Model Control System
- **Full Pipeline Control**: Override models for all 3 stages with dedicated flags
- **100% FREE Default**: All stages default to `deepseek/deepseek-chat-v3.1:free`
- **Multiple LLM Providers**: Support for DeepSeek (paid), OpenRouter (free DeepSeek + premium models)
- **Smart Fallbacks**: Automatic failover to premium models (Gemini 2.5, paid DeepSeek) on free model failures
- **Retry Logic**: 3 automatic attempts with exponential backoff before fallback activation

#### Available Command Line Flags:
- `--extract-model`: Control prompt extraction stage (LLM-1) - defaults to FREE DeepSeek
- `--generate-model`: Control article generation stage (LLM-2) - defaults to FREE DeepSeek
- `--editorial-model`: Control editorial review and cleanup stage (LLM-3) - defaults to FREE DeepSeek
- `--provider`: Force specific provider (deepseek or openrouter)
- `--no-publish`: Skip WordPress publication (by default articles are published automatically)

### 🔗 OpenRouter Integration
- **FREE DeepSeek Models**: Access to `deepseek/deepseek-chat-v3.1:free` via OpenRouter (ZERO cost!)
- **Premium Models**: OpenAI (GPT-4o, GPT-4o-mini), Google Gemini 2.5 Flash Lite via OpenRouter
- **Smart Routing**: Automatic routing between free and premium models based on availability
- **Single API Key**: Just add OPENROUTER_API_KEY to access both free and premium models

### 💰 Enhanced Token Tracking System
- **Zero-Cost Monitoring**: Track when FREE vs PREMIUM models are used
- **Retry Analytics**: Monitor retry attempts and fallback model usage
- **Model Performance**: Track which models succeed/fail for optimization
- **Cost Analysis**: Separate tracking for free operations vs premium fallbacks
- **Session Summaries**: Detailed reports including model types, attempts, and actual costs
- **Real-time Logging**: Live monitoring with model switching notifications

### 🔧 Content Cleaning Optimization
- **Enhanced Firecrawl API Configuration**: Added `excludeTags` and `includeTags` for precise content filtering
- **Improved Regex Patterns**: Fixed image removal, enhanced UI element detection, added social media filtering
- **Structural Content Cleaning**: Added duplicate block removal and minimum line length filtering
- **Content Quality Metrics**: Real-time tracking of cleaning efficiency with before/after statistics
- **Smart Navigation Filtering**: Automatic removal of repetitive navigation elements and UI clutter

### ✅ Previous Updates (January 2025)
- **Full LLM Request/Response Logging**: All interactions with DeepSeek API are now logged for debugging
- **Robust JSON Parsing**: Fixed "Extra data" and "Failed to parse JSON" errors with multiple parsing strategies  
- **Improved Prompts**: Enhanced prompt engineering with clear examples and format specifications
- **Complete Audit Trail**: Every LLM call is saved with timestamps, parameters, and raw responses

## Project Documentation

- **[LLM Models & Providers Guide](llm-models.md):** 🎛️ **Complete guide** to multi-provider LLM system, model selection, and command-line configuration.
- **[Technical Pipeline Flow](pipeline-flow.md):** 🔧 **Comprehensive technical breakdown** of all 10 stages with data structures, LLM interactions, and processing logic.
- **[Detailed Flow Description](flow.md):** A step-by-step breakdown of the entire pipeline, from the initial request to the final cleaned content.
- **[Configuration Guide](configuration.md):** Instructions on how to configure the project, including API keys, scoring weights, and domain filters.
- **[LLM Debugging Guide](llm-debugging.md):** Complete guide to understanding and debugging LLM interactions.
- **[Troubleshooting](troubleshooting.md):** Common issues and solutions for the content generation pipeline.

## Quick Start

1.  **Install Dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Set API Keys:**
    -   Copy your API keys into the `.env` file:
        ```
        FIRECRAWL_API_KEY=your_firecrawl_key_here
        OPENROUTER_API_KEY=your_openrouter_key_here  # MAIN KEY - provides FREE DeepSeek + Premium models
        DEEPSEEK_API_KEY=your_deepseek_key_here      # Optional - only for fallback scenarios
        ```

3.  **Setup WordPress Integration (Optional):**
    ```bash
    # Create 'prompts' category in WordPress
    python3 create_prompts_category.py
    
    # Test WordPress integration
    python3 test_publication_auto.py
    ```

4.  **Run the Pipeline:**
    ```bash
    # Single topic processing (100% FREE + WordPress auto-publish)
    python main.py "Your topic of interest"

    # Generate without WordPress publication (still FREE)
    python main.py "Your topic" --no-publish

    # Override to premium models (if you want to pay for higher quality)
    python main.py "Your topic" --generate-model "deepseek-reasoner"
    python main.py "Your topic" --generate-model "openai/gpt-4o-mini"

    # Maximum FREE mode - all stages use free models
    python main.py "Your topic" --extract-model "deepseek/deepseek-chat-v3.1:free" \
                                --generate-model "deepseek/deepseek-chat-v3.1:free" \
                                --editorial-model "deepseek/deepseek-chat-v3.1:free"

    # BATCH PROCESSING - Process multiple topics (FREE by default)
    python main.py --batch topics_prompts.txt

    # Batch processing without WordPress publication
    python main.py --batch topics_prompts.txt --no-publish

    # See all available options
    python main.py --help
    ```

5.  **Find the Results:**
    -   All results, including intermediate artifacts and final cleaned articles, will be saved in the `output/` directory, organized by topic.
    -   **WordPress Publication**: By default, publication results are saved in `wordpress_publication_result.json` (use `--no-publish` to disable)
    -   **LLM Logs**: Request/response logs are saved in `llm_requests/` and `llm_responses_raw/` subdirectories.
    -   **Token Reports**: Token usage reports are automatically generated as `token_usage_report.json` with detailed analytics.

## Pipeline Stages

The pipeline consists of 8 automated stages:

1. **Search**: Find relevant URLs using Firecrawl Search API
2. **Parsing**: Extract and clean content from found URLs  
3. **Scoring**: Score sources by trust, relevance, and depth
4. **Selection**: Select top 5 sources for analysis
5. **Cleaning**: Clean and optimize content for LLM processing
6. **Prompt Extraction**: Extract prompts from articles using LLM
7. **Article Generation**: Generate complete WordPress article using LLM
8. **WordPress Publication** (Default): Automatically publish article to WordPress with SEO metadata

## Batch Processing System

### Features
- **Sequential Processing**: Processes topics one by one, strictly in order
- **WordPress Verification**: Waits for WordPress publication confirmation before next topic
- **Memory Management**: Built-in memory monitoring and cleanup between topics
- **Progress Tracking**: Saves progress and can resume interrupted sessions
- **Content Types**: Supports different content types with separate configurations
- **Error Handling**: Retry mechanism for failed topics with configurable limits

### Usage Examples
```bash
# Basic batch processing
python main.py --batch topics_prompts.txt

# With custom content type and resume
python main.py --batch topics_business.txt --content-type business_ideas --resume

# Skip WordPress publication for all topics
python main.py --batch topics_prompts.txt --no-publish

# Custom models for batch processing
python main.py --batch topics_prompts.txt --generate-model "openai/gpt-4o" --editorial-model "deepseek-reasoner"
```

### Topics File Format
```
# Comments start with #
# One topic per line

prompts for creative design inspiration
prompts for business plan development
prompts for educational content creation
```

### Configuration Files
- **`batch_config.py`**: Main configuration for timeouts, memory limits, retry policies
- **`topics_prompts.txt`**: Example topics file for prompt-related content
- **Progress files**: `.batch_progress_{content_type}.json` for tracking progress
- **Lock files**: `.batch_lock_{content_type}.pid` to prevent concurrent runs

## LLM Interaction Logging & Token Tracking

Every LLM call is automatically logged with:
- **Request Data**: Full prompt, model parameters, timestamps
- **Response Data**: Raw LLM output before JSON parsing
- **Token Usage**: Detailed breakdown including reasoning tokens and cache hits
- **Metadata**: Stage info, topic, request IDs for tracking
- **Error Context**: Failed parsing attempts and debugging info

### Token Usage Analytics

The pipeline automatically tracks and reports:
- **Per-Request Tokens**: Prompt, completion, and reasoning tokens for each API call
- **Stage Breakdown**: Token consumption by pipeline stage (extraction, generation, etc.)
- **Session Summary**: Total tokens used across entire pipeline run
- **Performance Metrics**: Average tokens per request and session duration
- **DeepSeek Features**: Reasoning token tracking and cache utilization

### Directory Structure with LLM Logs & Token Reports:
```
output/Your_Topic/
├── token_usage_report.json                 # NEW: Complete token analytics
├── 06_extracted_prompts/
│   ├── all_prompts.json                    # Final results
│   ├── llm_requests/                       # What was sent to LLM
│   │   ├── source_1_request.json
│   │   └── source_2_request.json
│   └── llm_responses_raw/                  # Raw LLM responses  
│       ├── source_1_response.txt
│       └── source_2_response.txt
├── 07_final_article/
│   ├── wordpress_data.json
│   ├── article_content.html
│   ├── llm_requests/
│   └── llm_responses_raw/
└── ... (all stages with comprehensive logging)
```

### Example Token Usage Report:
```json
{
  "session_summary": {
    "total_requests": 6,
    "total_prompt_tokens": 25420,
    "total_completion_tokens": 8943,
    "total_tokens": 34363,
    "total_reasoning_tokens": 5791,
    "session_duration_minutes": 8.5,
    "average_tokens_per_request": 5727.2
  },
  "stage_breakdown": {
    "extract_prompts": {
      "requests": 5,
      "total_tokens": 23125,
      "reasoning_tokens": 4634
    },
    "generate_wordpress_article": {
      "requests": 1,
      "total_tokens": 11238,
      "reasoning_tokens": 1157
    }
  }
}
```
