# Troubleshooting Guide

This guide covers configuration and optimization tips for the Content Generation Pipeline with multi-provider LLM system (September 2025).

## 📋 Table of Contents

1. [Multi-Provider LLM Configuration](#1-multi-provider-llm-configuration) - Provider setup and troubleshooting
2. [Performance Optimization](#2-performance-optimization) - Speed and efficiency tuning
3. [Content Quality Optimization](#3-content-quality-optimization) - Improving output quality
4. [Configuration Validation](#4-configuration-validation) - Verify your setup

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

### 2. Performance Optimization

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

### 3. Content Quality Optimization

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

### 4. Configuration Validation

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