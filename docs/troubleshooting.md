# Troubleshooting Guide

This guide covers configuration and optimization tips for the Content Generation Pipeline with multi-provider LLM system (September 2025).

## 📋 Table of Contents

1. [Multi-Provider LLM Configuration](#1-multi-provider-llm-configuration) - Provider setup and troubleshooting
2. [JSON Parsing Issues](#2-json-parsing-issues) - Common LLM response parsing problems
3. [Performance Optimization](#3-performance-optimization) - Speed and efficiency tuning
4. [Content Quality Optimization](#4-content-quality-optimization) - Improving output quality
5. [Configuration Validation](#5-configuration-validation) - Verify your setup

## 🛠️ Configuration & Optimization

### 1. Multi-Provider LLM Configuration

**Problem**: Provider-specific errors with DeepSeek or OpenRouter

**Symptoms**:
- `API key not found for provider openrouter`
- Model not recognized warnings
- Different response formats between providers

**Setup Requirements**:
1. **API Keys**: Add both keys to `.env` file:
   ```bash
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
   FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. **Test Provider Connection**:
   ```python
   from src.llm_processing import get_llm_client
   
   # Test DeepSeek
   deepseek_client = get_llm_client("deepseek-reasoner")
   print("✅ DeepSeek connected")
   
   # Test OpenRouter (OpenAI)
   openrouter_client = get_llm_client("openai/gpt-4o-mini")
   print("✅ OpenRouter connected")
   ```

3. **Model Selection Examples**:
   ```bash
   # Default (DeepSeek for all)
   python3 main.py "your topic"
   
   # Use OpenAI for generation
   python3 main.py "your topic" --generate-model "openai/gpt-4o-mini"
   
   # Mix providers
   python3 main.py "your topic" --extract-model "deepseek-chat" --generate-model "openai/gpt-4o"
   ```

4. **Provider Detection**:
   ```python
   from src.config import get_provider_for_model
   print(get_provider_for_model('openai/gpt-4o-mini'))  # -> "openrouter"
   print(get_provider_for_model('deepseek-reasoner'))   # -> "deepseek"
   ```

---

### 2. JSON Parsing Issues

**Problem**: LLM returns malformed JSON causing parsing failures

**Symptoms**:
- Log shows "⚠️ source_X extracted 0 prompts - possible JSON parsing issue"
- Low extraction success rate (e.g., "4/10 prompts extracted (40% success rate)")
- JSON parsing errors in logs
- Editorial review falls back to original data

**Common Causes**:

1. **Escape Character Issues** (Most Common):
   - LLM returns JSON with `\"` instead of `"`
   - Example: `"prompt\_text": "content"` instead of `"prompt_text": "content"`
   - **Solution**: The system now automatically fixes these issues, but you can verify in `llm_responses_raw/` files

2. **Mixed JSON Formats**:
   - Some responses wrap JSON in code blocks (```json)
   - Some use different quote styles
   - **Solution**: Parser handles multiple formats automatically

3. **Control Character Issues** ⚡ **NEW FIX (Sept 2025)**:
   - LLM generates JSON with unescaped newlines, tabs, and other control characters
   - Example: JSON contains literal `\n` instead of `\\n`
   - Error: `"Invalid control character at: line X column Y"`
   - **Solution**: Enhanced parser with manual field extraction fallback

4. **Prompt Instructions Issue**:
   - Fixed in latest version: prompt now explicitly instructs to use standard JSON formatting
   - **Check**: Ensure `prompts/prompt_collection/01_extract.txt` contains updated instructions

**⚡ NEW: Enhanced Error Recovery (Sept 2025)**:

When JSON parsing fails due to control characters, the system now:
1. Attempts standard JSON parsing
2. Tries enhanced cleanup with regex-based field extraction
3. Falls back to manual data extraction using pattern matching
4. Preserves all LLM-generated content even if JSON structure is malformed

**Example Fix Applied**:
```
Before: ❌ JSON parsing failed → fallback to original dirty data
After:  ✅ Manual extraction → WordPress tags cleaned, all fields preserved
```

**Debugging Steps**:

1. **Check Raw Responses**:
   ```bash
   # View raw LLM responses for debugging
   ls output/[topic]/06_extracted_prompts/llm_responses_raw/
   cat output/[topic]/06_extracted_prompts/llm_responses_raw/source_1_response.txt
   ```

2. **Monitor Extraction Stats**:
   - Pipeline now logs detailed extraction statistics
   - Look for warnings about 0-prompt extractions
   - Success rate should be >80% for healthy runs

3. **Manual JSON Validation**:
   ```bash
   # Test if response is valid JSON
   python3 -c "import json; print(json.loads(open('source_1_response.txt').read()))"
   ```

**Expected Behavior**:
- Each source should extract exactly 2 prompts
- Total: 10 prompts from 5 sources
- Success rate should be 100% with fixed parser

---

### 3. Performance Optimization

**Performance Tuning Options**:

1. **Concurrent Processing** (`src/config.py`):
   ```python
   CONCURRENT_REQUESTS = 8  # Default: 5, increase for faster scraping
   ```

2. **Content Selection** (`src/config.py`):
   ```python
   TOP_N_SOURCES = 3        # Default: 5, fewer sources = faster processing
   MIN_CONTENT_LENGTH = 8000  # Default: 10000, lower = more sources
   ```

3. **Model Selection for Speed**:
   ```bash
   # Fast extraction + quality generation
   python3 main.py "topic" --extract-model "deepseek-chat" --generate-model "openai/gpt-4o-mini"
   ```

4. **Source Quality**:
   - Add trusted domains to `filters/trusted_sources.json`
   - Block low-quality domains in `filters/blocked_domains.json`

**Performance Monitoring**:
```bash
# Check token usage
cat "output/Your_Topic/token_usage_report.json"

# Monitor processing time
tail -f pipeline.log
```

---

### 4. Content Quality Optimization

**Quality Enhancement Strategies**:

1. **Source Selection Optimization** (`src/config.py`):
   ```python
   # Scoring weights (should sum to 1.0)
   TRUST_SCORE_WEIGHT = 0.5     # Domain authority
   RELEVANCE_SCORE_WEIGHT = 0.3  # Keyword matching
   DEPTH_SCORE_WEIGHT = 0.2      # Content length
   ```

2. **Trusted Sources** (`filters/trusted_sources.json`):
   ```json
   {
     "techcrunch.com": 2.2,
     "ai.googleblog.com": 2.5,
     "arxiv.org": 2.9
   }
   ```

3. **Model Selection for Quality**:
   ```bash
   # Best quality (slower)
   python3 main.py "topic" --extract-model "deepseek-reasoner" --generate-model "openai/gpt-4o"
   
   # Balanced quality/speed
   python3 main.py "topic" --generate-model "openai/gpt-4o-mini"
   ```

4. **Debugging Quality Issues**:
   ```bash
   # Check LLM interactions
   ls "output/Your_Topic/*/llm_requests/"
   ls "output/Your_Topic/*/llm_responses_raw/"
   
   # Review extracted prompts
   cat "output/Your_Topic/06_extracted_prompts/all_prompts.json"
   ```

---

---

### 5. Configuration Validation

**System Health Check**:

1. **Verify API Keys**:
   ```python
   import os
   print("Firecrawl:", "✅" if os.getenv("FIRECRAWL_API_KEY") else "❌")
   print("DeepSeek:", "✅" if os.getenv("DEEPSEEK_API_KEY") else "❌")
   print("OpenRouter:", "✅" if os.getenv("OPENROUTER_API_KEY") else "❌")
   ```

2. **Test Pipeline**:
   ```bash
   # Quick test run
   python3 main.py "AI testing"
   
   # Check output structure
   ls -la "output/AI_testing/"
   ```

3. **Monitor Results**:
   ```bash
   # View pipeline logs
   tail -f pipeline.log
   
   # Check token usage
   cat "output/Your_Topic/token_usage_report.json"
   
   # Review generated content
   cat "output/Your_Topic/09_final_article/article_content.html"
   ```

4. **Configuration Check**:
   ```python
   from src import config
   print(f"Min content length: {config.MIN_CONTENT_LENGTH}")
   print(f"Concurrent requests: {config.CONCURRENT_REQUESTS}")
   print(f"Top sources: {config.TOP_N_SOURCES}")
   print(f"Default models: {config.LLM_MODELS}")
   ```

---

## ⚡ Quick Commands

### Reset Pipeline
```bash
# Remove output for specific topic
rm -rf "output/Your_Topic"

# Clean all outputs
rm -rf output/*

# Restart pipeline
python3 main.py "your topic"
```

### Available Commands
```bash
# Default (DeepSeek for all)
python3 main.py "topic"

# Model overrides
python3 main.py "topic" --extract-model "deepseek-chat"
python3 main.py "topic" --generate-model "openai/gpt-4o-mini"
python3 main.py "topic" --provider deepseek

# Help
python3 main.py --help
```

---

## 📊 Output Structure

Pipeline creates organized output for each topic:

```
output/Your_Topic/
├── token_usage_report.json          # Token analytics
├── 01_search/                       # Search results
├── 02_parsing/                      # Scraped content
├── 03_scoring/                      # Source scoring
├── 04_selection/                    # Selected sources
├── 05_cleaning/                     # Cleaned content
├── 06_extracted_prompts/            # LLM extraction
│   ├── all_prompts.json
│   ├── llm_requests/               # Debug logs
│   └── llm_responses_raw/
└── 07_final_article/               # Final output
    ├── wordpress_data.json         # Complete data
    ├── article_content.html        # HTML content
    ├── llm_requests/
    └── llm_responses_raw/
```

---

## 📚 Related Documentation

- **[LLM Models & Providers Guide](llm-models.md)** - Complete multi-provider setup
- **[Configuration Guide](configuration.md)** - All configuration options
- **[LLM Debugging Guide](llm-debugging.md)** - Detailed LLM interaction analysis
- **[Main README](README.md)** - Quick start and overview

---

*For technical implementation details, see source code in `src/` directory.*