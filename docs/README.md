# AI-Powered Content Generation Pipeline

This project is an automated pipeline for generating high-quality content based on a given topic. It leverages the Firecrawl API to search for relevant sources, scrapes their content, scores them based on a set of criteria, and cleans the best articles for final use.

## Latest Updates (September 2025)

### 🎛️ Flexible Model Configuration System
- **Per-Function Model Selection**: Configure different models for each LLM function
- **Easy Model Switching**: Change models through config file without code changes
- **Backward Compatibility**: All functions default to `deepseek-reasoner`
- **Extensible Architecture**: Ready for new functions with their own model preferences

### 💰 Token Tracking System
- **Comprehensive Token Monitoring**: Track token usage for every LLM request with detailed breakdowns
- **Session Summaries**: Automatic generation of token usage reports per pipeline run
- **DeepSeek Integration**: Full support for reasoning tokens and cache information  
- **Stage-wise Analytics**: Token consumption analysis by pipeline stage
- **Real-time Logging**: Live token usage monitoring during pipeline execution

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

2.  **Set API Key:**
    -   Copy your Firecrawl API key into the `.env` file:
        ```
        FIRECRAWL_API_KEY=your_api_key_here
        ```

3.  **Run the Pipeline:**
    ```bash
    # Full pipeline (all 10 stages)
    python main.py "Your topic of interest"
    
    # Stop at specific stage for debugging
    python main.py "Your topic of interest" --stage 7
    ```

4.  **Find the Results:**
    -   All results, including intermediate artifacts and final cleaned articles, will be saved in the `output/` directory, organized by topic.
    -   **NEW**: LLM request/response logs are saved in `llm_requests/` and `llm_responses_raw/` subdirectories.
    -   **NEW**: Token usage reports are automatically generated as `token_usage_report.json` with detailed analytics.

## Pipeline Stages

The pipeline consists of 10 stages that can be executed individually for debugging:

1. **Search** (`--stage 1`): Find relevant URLs using Firecrawl Search API
2. **Parsing** (`--stage 2-6`): Extract and clean content from found URLs  
3. **Prompt Extraction** (`--stage 7`): Extract prompts from articles using LLM
4. **Ranking** (`--stage 8`): Rank and select best prompts using LLM
5. **Enrichment** (`--stage 9`): Generate examples and commentary using LLM
6. **Assembly** (`--stage 10`): Assemble final article using LLM

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
