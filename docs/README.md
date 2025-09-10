# AI-Powered Content Generation Pipeline

This project is an automated pipeline for generating high-quality content based on a given topic. It leverages the Firecrawl API to search for relevant sources, scrapes their content, scores them based on a set of criteria, and cleans the best articles for final use.

## Latest Updates (January 2025)

### ✅ Enhanced LLM Debugging & Transparency
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

## Pipeline Stages

The pipeline consists of 10 stages that can be executed individually for debugging:

1. **Search** (`--stage 1`): Find relevant URLs using Firecrawl Search API
2. **Parsing** (`--stage 2-6`): Extract and clean content from found URLs  
3. **Prompt Extraction** (`--stage 7`): Extract prompts from articles using LLM
4. **Ranking** (`--stage 8`): Rank and select best prompts using LLM
5. **Enrichment** (`--stage 9`): Generate examples and commentary using LLM
6. **Assembly** (`--stage 10`): Assemble final article using LLM

## LLM Interaction Logging

Every LLM call is automatically logged with:
- **Request Data**: Full prompt, model parameters, timestamps
- **Response Data**: Raw LLM output before JSON parsing
- **Metadata**: Stage info, topic, request IDs for tracking
- **Error Context**: Failed parsing attempts and debugging info

### Directory Structure with LLM Logs:
```
output/Your_Topic/
├── 06_extracted_prompts/
│   ├── all_prompts.json                    # Final results
│   ├── llm_requests/                       # NEW: What was sent to LLM
│   │   ├── source_1_request.json
│   │   └── source_2_request.json
│   └── llm_responses_raw/                  # NEW: Raw LLM responses  
│       ├── source_1_response.txt
│       └── source_2_response.txt
├── 07_ranked_prompts/
│   ├── best_prompts.json
│   ├── llm_requests/
│   └── llm_responses_raw/
└── ... (similar structure for stages 8-10)
```
