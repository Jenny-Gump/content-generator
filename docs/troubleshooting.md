# Troubleshooting Guide

This guide covers common issues and solutions when using the Content Generation Pipeline, with focus on multi-provider LLM system (September 2025) and previous LLM enhancements.

## 🚨 Common Issues

### 🆕 Multi-Provider LLM Issues (September 2025)

#### 1. API Key Not Found Error

**Problem**: `ValueError: API key not found for provider openrouter. Check OPENROUTER_API_KEY in .env`

**Symptoms**:
- Pipeline fails when trying to use OpenAI models
- Error occurs during client creation

**Solutions**:
1. **Add missing API key** to `.env`:
   ```bash
   echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" >> .env
   ```
2. **Verify key format**:
   - DeepSeek: `sk-xxxxxxxx...`
   - OpenRouter: `sk-or-v1-xxxxxxxx...`

3. **Check environment loading**:
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv('OPENROUTER_API_KEY'))  # Should not be None
   ```

#### 2. Model Not Recognized

**Problem**: Model falls back to default provider unexpectedly

**Symptoms**:
- Command line model override ignored
- Logs show: `Model "custom-model" -> Provider: deepseek (fallback)`

**Solutions**:
1. **Check available models**:
   ```python
   from src.config import LLM_PROVIDERS
   print(LLM_PROVIDERS['openrouter']['models'])
   ```
2. **Use exact model names**:
   - ✅ Correct: `openai/gpt-4o-mini`
   - ❌ Wrong: `gpt-4o-mini`

#### 3. OpenRouter API Errors

**Problem**: HTTP errors when using OpenRouter

**Symptoms**:
- `HTTP 401 Unauthorized`
- `HTTP 429 Rate Limited`
- Connection timeouts

**Solutions**:
1. **Verify API key validity** at [OpenRouter dashboard](https://openrouter.ai/keys)
2. **Check account balance** for paid models
3. **Retry with exponential backoff** (built into OpenAI client)
4. **Switch to DeepSeek temporarily**:
   ```bash
   python main.py "topic" --extract-model "deepseek-chat"
   ```

---

### 2. LLM JSON Parsing Errors

**Problem**: `Failed to parse extracted JSON string: Extra data: line X column Y`

**Symptoms**:
- Pipeline stops at stage 7 (extraction)
- Log shows JSON parsing failures
- Empty results in `all_prompts.json`

**Solutions**:
1. **Check raw LLM response**:
   ```bash
   cat "output/Your_Topic/06_extracted_prompts/llm_responses_raw/source_1_response.txt"
   ```
2. **Look for malformed JSON**:
   - Missing quotes around strings
   - Unescaped quotes in content
   - Trailing commas
   - Extra text before/after JSON

3. **Use debug mode**:
   ```bash
   python main.py "Your topic" --stage 7
   ```

**Prevention**:
- The robust parser handles most common JSON errors automatically
- Check `prompts/prompt_collection/01_extract.txt` for clear JSON format instructions

---

### 2. Empty LLM Responses

**Problem**: LLM returns empty or invalid responses

**Symptoms**:
- `Error generating example` in results
- Empty files in `llm_responses_raw/`
- Pipeline continues but with poor quality outputs

**Solutions**:
1. **Check API key**: Verify `DEEPSEEK_API_KEY` in `.env`
2. **Check rate limits**: API might be throttling requests
3. **Review prompts**: Examine files in `prompts/prompt_collection/`
4. **Check request logs**:
   ```bash
   cat "output/Your_Topic/*/llm_requests/*_request.json"
   ```

**Debugging steps**:
1. Test API connection manually
2. Reduce concurrent processing
3. Check for timeout issues in logs

---

### 3. Firecrawl API Issues

**Problem**: Search or scraping fails

**Symptoms**:
- `No URLs found in search results`
- `No valid sources found after scraping`
- Pipeline stops at early stages (1-6)

**Solutions**:
1. **Check API key**: Verify `FIRECRAWL_API_KEY` in `.env`
2. **Check rate limits**: Reduce `CONCURRENT_REQUESTS` in `src/config.py`
3. **Review blocked domains**: Check `filters/blocked_domains.json`
4. **Adjust content length**: Lower `MIN_CONTENT_LENGTH` in `src/config.py`

---

### 4. Stage-Specific Debugging

**Problem**: Need to debug specific pipeline stage

**Solutions**:

#### Stage 7 (Prompt Extraction)
```bash
python main.py "Your topic" --stage 7
```
- Check: `06_extracted_prompts/llm_requests/`
- Check: `06_extracted_prompts/llm_responses_raw/`
- Look for: JSON format issues, empty responses

#### Stage 8 (Ranking)
```bash
python main.py "Your topic" --stage 8
```
- Check: `07_ranked_prompts/llm_requests/rank_prompts_request.json`
- Check: `07_ranked_prompts/llm_responses_raw/rank_prompts_response.txt`
- Look for: Ranking logic issues, insufficient prompts

#### Stage 9 (Enrichment)
```bash
python main.py "Your topic" --stage 9
```
- Check: `08_enriched_prompts/llm_requests/`
- Look for: Failed example generation, commentary errors

#### Stage 10 (Assembly)
```bash
python main.py "Your topic" --stage 10
```
- Check: `09_final_article/llm_requests/assemble_article_request.json`
- Check: `09_final_article/llm_responses_raw/assemble_article_response.txt`

---

### 5. Performance Issues

**Problem**: Pipeline runs too slowly

**Solutions**:
1. **Increase concurrency**:
   ```python
   # In src/config.py
   CONCURRENT_REQUESTS = 8  # Default: 5
   ```

2. **Reduce content processing**:
   ```python
   # In src/config.py
   TOP_N_SOURCES = 3      # Default: 5
   MIN_CONTENT_LENGTH = 8000  # Default: 10000
   ```

3. **Optimize source selection**:
   - Add more trusted sources to `filters/trusted_sources.json`
   - Update blocked domains in `filters/blocked_domains.json`

---

### 6. Content Quality Issues

**Problem**: Generated content is low quality

**Symptoms**:
- Poor prompts extracted
- Irrelevant examples
- Generic commentary

**Solutions**:
1. **Improve source selection**:
   - Adjust scoring weights in `src/config.py`
   - Add domain-specific trusted sources
   - Review topic formulation

2. **Enhance prompts**:
   - Edit `prompts/prompt_collection/*.txt` files
   - Add better examples
   - Improve instructions clarity

3. **Debug LLM interactions**:
   - Review request/response logs
   - Test prompts manually with DeepSeek API
   - A/B test different prompt variations

---

## 🔍 Diagnostic Commands

### Check Pipeline Status
```bash
# View all output directories
ls -la output/

# Check specific stage results
ls -la "output/Your_Topic/"

# View recent logs
tail -100 pipeline.log
```

### Examine LLM Interactions
```bash
# Count total LLM requests
find output/ -name "*_request.json" | wc -l

# Find failed requests
grep -r "Error" output/*/llm_responses_raw/

# Check request timestamps
find output/ -name "*_request.json" -exec grep -l "timestamp" {} \;
```

### API Health Check
```bash
# Test Firecrawl connection (requires curl and jq)
curl -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  "https://api.firecrawl.dev/v2/search?query=test"

# Check DeepSeek API status
# (Manual testing required via their dashboard)
```

---

## ⚡ Quick Fixes

### Reset Pipeline
```bash
# Remove problematic output
rm -rf "output/Your_Topic"

# Restart from beginning
python main.py "Your topic"
```

### Clean Logs
```bash
# Archive old logs
mv pipeline.log pipeline.log.backup
touch pipeline.log

# Clear old LLM interaction logs
find output/ -name "llm_*" -type d -exec rm -rf {} +
```

### Update Configuration
```bash
# Reset to defaults
cp src/config.py.example src/config.py  # if backup exists

# Test with minimal configuration
python main.py "simple test topic" --stage 7
```

---

## 📊 Monitoring & Analysis

### Success Rate Analysis
```bash
# Count successful extractions
find output/ -name "all_prompts.json" -exec wc -l {} \;

# Count failed responses
grep -r "Error generating" output/

# Check parsing success rate
grep -r "Failed to parse" logs/
```

### Performance Metrics
```bash
# Average processing time per stage
grep "Pipeline stopped\|Pipeline Finished" pipeline.log

# LLM response times (check timestamps in request files)
find output/ -name "*_request.json" -exec grep "timestamp" {} \;
```

---

## 🆘 Getting Help

If you encounter issues not covered in this guide:

1. **Check logs first**: `pipeline.log` and `logs/operations.jsonl`
2. **Enable debug mode**: Run with `--stage` to isolate problems
3. **Examine LLM logs**: All requests/responses are saved for analysis
4. **Test components**: Verify API keys and network connectivity
5. **Review configuration**: Ensure settings match your use case

### Debug Information to Collect

When reporting issues, include:
- Topic used: `"Your exact topic string"`
- Stage where failure occurred: `--stage X`
- Error messages from `pipeline.log`
- Sample request file: `llm_requests/*.json`
- Sample response file: `llm_responses_raw/*.txt`
- Configuration settings: `src/config.py` values

---

## 🔧 Advanced Troubleshooting

### Custom Prompt Testing
```python
# Test prompt extraction manually
from src.llm_processing import extract_prompts_from_article

article_text = "Your test article content here..."
prompts = extract_prompts_from_article(
    article_text=article_text,
    topic="test topic",
    base_path="debug_test"
)
print(prompts)
```

### JSON Parser Testing
```python
# Test JSON parsing with problematic response
from src.llm_processing import _parse_json_from_response

response = """{"prompt_text": "test", "extra": "data"}"""
result = _parse_json_from_response(response)
print(result)
```

### Configuration Validation
```python
# Verify configuration values
from src import config
print(f"Min content length: {config.MIN_CONTENT_LENGTH}")
print(f"Concurrent requests: {config.CONCURRENT_REQUESTS}")
print(f"Top sources: {config.TOP_N_SOURCES}")
```

---

This troubleshooting guide covers the most common issues with the enhanced Content Generation Pipeline. For additional help, refer to the [LLM Debugging Guide](llm-debugging.md) for detailed analysis of LLM interactions.