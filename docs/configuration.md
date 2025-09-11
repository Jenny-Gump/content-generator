# Configuration Guide

This project can be customized through the `.env` file, the `src/config.py` file, and the JSON files in the `filters/` directory.

## 🆕 Flexible Model Configuration (September 2025)

### **Per-Function Model Selection**
The system now supports configurable models for each LLM function:
- **Extract Prompts**: Configurable model for prompt extraction from articles
- **Generate Article**: Configurable model for WordPress article generation
- **Easy Model Switching**: Change models per function without code changes
- **Backward Compatibility**: All functions default to `deepseek-reasoner`

### **Previous Enhancements (January 2025)**
- **DeepSeek API integration** for prompt extraction, ranking, and enrichment
- **Full request/response logging** for debugging LLM interactions
- **Robust JSON parsing** with multiple fallback strategies
- **Stage-specific execution** using `--stage` parameter

## API Keys (`.env`)

This file stores the essential API keys for both Firecrawl and DeepSeek services.

-   **`FIRECRAWL_API_KEY`**: Your unique API key from Firecrawl for search and scraping operations.
-   **`DEEPSEEK_API_KEY`**: Your API key for DeepSeek LLM service (stages 7-10).

```
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Main Configuration (`src/config.py`)

This file contains all the operational parameters for the pipeline.

-   **`MIN_CONTENT_LENGTH`**: The minimum number of characters a scraped article must have to be considered valid. Articles shorter than this are discarded.
    -   *Default: `10000`*

-   **`CONCURRENT_REQUESTS`**: The number of concurrent requests sent to the Firecrawl Scrape API. Increasing this can speed up scraping, but may also lead to rate limiting.
    -   *Default: `5`*

-   **`TOP_N_SOURCES`**: The number of top-ranked articles to select for the final cleaning stage.
    -   *Default: `5`*

### **🆕 LLM Models Configuration**

-   **`LLM_MODELS`**: Dictionary mapping pipeline stages to their respective models.
    ```python
    LLM_MODELS = {
        "extract_prompts": "deepseek-reasoner",      # Model for prompt extraction
        "generate_article": "deepseek-reasoner",    # Model for article generation
    }
    ```
    
-   **`DEFAULT_MODEL`**: Fallback model used when no specific model is configured for a stage.
    -   *Default: `"deepseek-reasoner"`*

#### **How to Change Models for Different Functions:**

**Example 1: Use different models for different tasks**
```python
LLM_MODELS = {
    "extract_prompts": "deepseek-chat",          # Faster model for extraction
    "generate_article": "deepseek-reasoner",    # More powerful model for generation
}
```

**Example 2: Use GPT-4 for article generation** (requires OpenAI-compatible setup)
```python
LLM_MODELS = {
    "extract_prompts": "deepseek-reasoner",
    "generate_article": "gpt-4-turbo",         # Different model for final article
}
```

**Note**: Changing models requires compatible API endpoints. Current setup supports DeepSeek API. For other providers, you may need to modify the client configuration in `src/llm_processing.py`.

### Scoring Weights

These constants control the importance of each metric when calculating the final score for an article. The sum of these weights should ideally be `1.0`.

-   **`TRUST_SCORE_WEIGHT`**: The weight given to the trust score (based on `trusted_sources.json`).
    -   *Default: `0.5`*
-   **`RELEVANCE_SCORE_WEIGHT`**: The weight given to the relevance score (based on keyword matches).
    -   *Default: `0.3`*
-   **`DEPTH_SCORE_WEIGHT`**: The weight given to the depth score (based on content length).
    -   *Default: `0.2`*

## Filters (`filters/`)

These JSON files allow for fine-grained control over which sources are included or excluded.

### `blocked_domains.json`

This is a "blacklist" to immediately discard URLs from specific domains or that contain certain patterns.

-   **`domains`**: A list of domains to block entirely (e.g., `"youtube.com"`, `"reddit.com"`).
-   **`patterns`**: A list of string patterns. If a pattern is found anywhere in a URL, that URL will be blocked (e.g., `"/comments/"`, `"/login"`).

### `trusted_sources.json`

This is a "whitelist" that assigns a trust score multiplier to high-quality domains. The higher the number, the more weight the source will have in the final ranking. A standard, unlisted source has a default score of `1.0`.

-   **`"domain.com": score`**: The key is the domain name, and the value is its trust score multiplier.

**Example:**
```json
{
  "techcrunch.com": 2.2,
  "ai.googleblog.com": 2.5,
  "arxiv.org": 2.9
}
```

## Command Line Usage

### Basic Execution
```bash
# Full pipeline (all 10 stages)
python main.py "Your topic of interest"

# Examples
python main.py "Best prompts for data analysis"
python main.py "AI trends in 2025"
python main.py "Machine learning best practices"
```

### Stage-Specific Execution

Use the `--stage` parameter to stop at a specific stage for debugging:

```bash
# Stop after search and parsing (stages 1-6)
python main.py "AI automation tools" --stage 6

# Stop after prompt extraction (stage 7) - useful for debugging LLM responses
python main.py "Best prompts for analysis" --stage 7

# Stop after ranking (stage 8)
python main.py "Content generation techniques" --stage 8

# Stop after enrichment (stage 9)
python main.py "SEO optimization strategies" --stage 9

# Full execution (stage 10) - same as no --stage parameter
python main.py "Digital marketing trends" --stage 10
```

### LLM Configuration

The LLM processing uses the following default settings (configured in `src/llm_processing.py`):

- **Model**: `deepseek-reasoner` (DeepSeek R1 with Chain of Thought reasoning)
- **JSON Mode**: Enabled for structured outputs
- **Max Tokens**: 
  - Example generation: 200 tokens
  - Commentary generation: 150 tokens
  - Unlimited for extraction, ranking, and assembly
- **Temperature**: Default (typically 0.7)

## Output Structure

With LLM logging enabled, your output directory will have this structure:

```
output/Your_Topic/
├── 01_search/                          # Search results
├── 02_parsing/                         # Scraped and validated content
├── 03_scoring/                         # Scored sources
├── 04_selection/                       # Top 5 selected sources
├── 05_cleaning/                        # Cleaned content
├── 06_extracted_prompts/               # Stage 7: Prompt extraction
│   ├── all_prompts.json                # Final results
│   ├── llm_requests/                   # 🔍 Debug: Requests sent to LLM
│   │   ├── source_1_request.json
│   │   ├── source_2_request.json
│   │   └── ...
│   └── llm_responses_raw/              # 🔍 Debug: Raw LLM responses
│       ├── source_1_response.txt
│       ├── source_2_response.txt
│       └── ...
├── 07_ranked_prompts/                  # Stage 8: Prompt ranking
│   ├── best_prompts.json
│   ├── llm_requests/
│   │   └── rank_prompts_request.json
│   └── llm_responses_raw/
│       └── rank_prompts_response.txt
├── 08_enriched_prompts/                # Stage 9: Content enrichment
│   ├── enriched_prompts.json
│   ├── llm_requests/                   # 2 requests per prompt
│   │   ├── prompt_1_example_request.json
│   │   ├── prompt_1_commentary_request.json
│   │   └── ...
│   └── llm_responses_raw/
│       ├── prompt_1_example_response.txt
│       ├── prompt_1_commentary_response.txt
│       └── ...
└── 09_final_article/                   # Stage 10: Final article
    ├── final_article.md
    ├── llm_requests/
    │   └── assemble_article_request.json
    └── llm_responses_raw/
        └── assemble_article_response.txt
```

## Debugging LLM Issues

If you encounter LLM-related errors, use the debug logs:

1. **Check what was sent to LLM**: Look at files in `llm_requests/` directories
2. **Check raw LLM responses**: Look at files in `llm_responses_raw/` directories
3. **Use stage-specific execution**: Run `--stage 7` to debug prompt extraction
4. **Review prompts**: Check `prompts/prompt_collection/` for prompt templates

For detailed debugging guide, see [LLM Debugging Guide](llm-debugging.md).

## Performance Tuning

### Concurrent Processing
- Adjust `CONCURRENT_REQUESTS` in `src/config.py` based on your API limits
- Higher values = faster processing but potential rate limiting
- Recommended: Start with 5, increase gradually if stable

### Content Quality
- Adjust `MIN_CONTENT_LENGTH` to filter short/low-quality articles
- Increase for more selective content, decrease to include more sources
- Recommended: 8000-12000 characters for high-quality content

### Source Selection
- Modify `TOP_N_SOURCES` to change final selection size
- More sources = more comprehensive but slower LLM processing
- Recommended: 3-7 sources for optimal balance
