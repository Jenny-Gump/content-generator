# LLM Models & Providers Guide

This guide covers the flexible multi-provider LLM system in the Content Generator pipeline. The system supports multiple providers with automatic retry logic and fallback models for maximum reliability.

## 🎛️ Multi-Provider Architecture with Reliability

The Content Generator supports multiple LLM providers through a unified interface:

- **OpenRouter**: Primary provider - gateway to Google Gemini 2.5 (65K tokens), OpenAI models, and **FREE DeepSeek models**
- **DeepSeek**: Alternative provider with reasoning capabilities
- **Retry Logic**: 3 automatic retries with exponential backoff (2s, 5s, 10s)
- **Fallback System**: Automatic model switching on failures
- **Extensible**: Easy to add new providers

## 📋 Configuration Overview

### Default Configuration (`src/config.py`)

```python
# Default models for each pipeline stage - ALL FREE!
LLM_MODELS = {
    "extract_prompts": "deepseek/deepseek-chat-v3.1:free",              # 🆓 FREE model for prompt extraction (LLM-1)
    "generate_article": "deepseek/deepseek-chat-v3.1:free",             # 🆓 FREE model for article generation (LLM-2)
    "editorial_review": "deepseek/deepseek-chat-v3.1:free",             # 🆓 FREE model for editorial review (LLM-3)
}

# Fallback models for each stage (used when primary model fails)
FALLBACK_MODELS = {
    "extract_prompts": "google/gemini-2.5-flash-lite-preview-06-17",    # Fallback to Gemini 2.5
    "generate_article": "deepseek-reasoner",                            # Fallback to paid DeepSeek if free fails
    "editorial_review": "google/gemini-2.5-flash-lite-preview-06-17",   # Fallback to Gemini 2.5
}

# Retry configuration for LLM requests
RETRY_CONFIG = {
    "max_attempts": 3,
    "delays": [2, 5, 10],  # seconds between retries
    "use_fallback_on_final_failure": True
}

# Default model if no specific model is configured
DEFAULT_MODEL = "deepseek-reasoner"
```

### Provider Configuration

```python
LLM_PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "models": ["deepseek-reasoner", "deepseek-chat"]
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "models": [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "google/gemini-2.0-flash-001",
            "google/gemini-2.5-flash-lite-preview-06-17",
            "deepseek/deepseek-chat-v3.1:free"  # 🆓 FREE DeepSeek model
        ]
    }
}
```

## 🔑 API Keys Setup

Add the following keys to your `.env` file:

```bash
# Primary key for FREE DeepSeek models + premium fallbacks
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx

# Required for Firecrawl search/scraping
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional - for direct DeepSeek access (fallback scenarios only)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note**: OPENROUTER_API_KEY is the main key providing both FREE DeepSeek models and premium fallbacks.

## 🚀 Command Line Usage

### Basic Usage

```bash
# Use default models (100% FREE DeepSeek for all tasks)
python main.py "Your topic"
```

### Model Overrides

```bash
# Override to premium model for article generation (from free default)
python main.py "Your topic" --generate-model "deepseek-reasoner"

# Use Gemini 2.5 for article generation instead of free DeepSeek
python main.py "Your topic" --generate-model "google/gemini-2.5-flash-lite-preview-06-17"

# Full pipeline with premium models for all 3 stages (instead of free defaults)
python main.py "Your topic" --extract-model "deepseek-reasoner" --generate-model "google/gemini-2.5-flash-lite-preview-06-17" --editorial-model "deepseek-reasoner"

# Force free models for all stages (already default, but explicit)
python main.py "Your topic" --extract-model "deepseek/deepseek-chat-v3.1:free" --generate-model "deepseek/deepseek-chat-v3.1:free" --editorial-model "deepseek/deepseek-chat-v3.1:free"

# See all available options
python main.py --help
```

### Available Command Line Flags

- `--extract-model MODEL` - Override model for prompt extraction (LLM-1)
- `--generate-model MODEL` - Override model for article generation (LLM-2)  
- `--editorial-model MODEL` - Override model for editorial review and cleanup (LLM-3)
- `--provider {deepseek,openrouter}` - Specify provider preference
- `--no-publish` - Skip WordPress publication (articles published by default)

## 📖 Available Models

### DeepSeek Models

| Model | Cost | Description | Best For |
|-------|------|-------------|----------|
| `deepseek/deepseek-chat-v3.1:free` | 🆓 **FREE** | Latest free model via OpenRouter | **Article generation - cost savings!** |
| `deepseek-reasoner` | 💰 Paid | Most capable with reasoning | Complex tasks, fallback choice |
| `deepseek-chat` | 💰 Paid | Faster conversational model | Quick extraction, speed-critical tasks |

### Google Gemini Models (via OpenRouter) - Fallback Models

| Model | Max Tokens | Description | Best For |
|-------|------------|-------------|----------|
| `google/gemini-2.5-flash-lite-preview-06-17` | **65,535** | Ultra-fast, high-capacity model | **Fallback for extraction/review** |
| `google/gemini-2.0-flash-001` | 8,192 | Fast multimodal model | ⚠️ Limited for long articles |

### OpenAI Models (via OpenRouter)

| Model | Max Tokens | Description | Best For |
|-------|------------|-------------|----------|
| `openai/gpt-4o` | 16,384 | Latest GPT-4 Omni | Highest quality generation |
| `openai/gpt-4o-mini` | 16,384 | Smaller, faster GPT-4 Omni | Balanced quality/speed |
| `openai/gpt-4-turbo` | 4,096 | GPT-4 Turbo | High-quality, fast processing |
| `openai/gpt-3.5-turbo` | 4,096 | Fast and cost-effective | Budget-conscious tasks |

## 🎯 Configuration Examples

### Example 1: Maximum Free Setup ⭐ **RECOMMENDED (DEFAULT)**
```python
LLM_MODELS = {
    "extract_prompts": "deepseek/deepseek-chat-v3.1:free",           # 🆓 FREE extraction (LLM-1)
    "generate_article": "deepseek/deepseek-chat-v3.1:free",          # 🆓 FREE generation (LLM-2)
    "editorial_review": "deepseek/deepseek-chat-v3.1:free",          # 🆓 FREE review (LLM-3)
}
```

### Example 2: Premium DeepSeek Setup
```python
LLM_MODELS = {
    "extract_prompts": "deepseek-reasoner",     # Premium reasoning extraction (LLM-1)
    "generate_article": "deepseek-reasoner",    # Premium reasoning generation (LLM-2)
    "editorial_review": "deepseek-reasoner",    # Premium reasoning cleanup (LLM-3)
}
```

### Example 3: Mixed Quality Setup
```python
LLM_MODELS = {
    "extract_prompts": "deepseek/deepseek-chat-v3.1:free",            # FREE extraction (LLM-1)
    "generate_article": "google/gemini-2.5-flash-lite-preview-06-17", # Premium generation (LLM-2)
    "editorial_review": "deepseek-reasoner",                          # Premium editing (LLM-3)
}
```

### Example 4: Fallback Override Setup 💰
```python
LLM_MODELS = {
    "extract_prompts": "google/gemini-2.5-flash-lite-preview-06-17",   # Premium extraction (LLM-1)
    "generate_article": "deepseek-reasoner",                          # Premium generation (LLM-2)
    "editorial_review": "google/gemini-2.5-flash-lite-preview-06-17",  # Premium review (LLM-3)
}
```

### Example 5: Command Line Premium Overrides
```bash
# Use premium DeepSeek Reasoner for editorial review (from free default)
python main.py "AI tools for content creators" --editorial-model "deepseek-reasoner"

# Premium generation with free extraction/review
python main.py "prompt engineering" --generate-model "google/gemini-2.5-flash-lite-preview-06-17"

# Full premium pipeline override
python main.py "content strategy" --extract-model "deepseek-reasoner" --generate-model "google/gemini-2.5-flash-lite-preview-06-17" --editorial-model "deepseek-reasoner"
```

## 🔄 Retry Logic & Fallback System

The system provides robust error handling with automatic retries and model fallbacks:

### Retry Configuration
- **3 automatic retries** per model with exponential backoff
- **Retry delays**: 2 seconds → 5 seconds → 10 seconds
- **Smart error detection**: Network issues, rate limits, model unavailability

### Fallback Models
If primary model fails after all retries, system automatically switches to fallback:
```python
FALLBACK_MODELS = {
    "extract_prompts": "google/gemini-2.5-flash-lite-preview-06-17",    # Fallback to Gemini 2.5
    "generate_article": "deepseek-reasoner",                            # Paid DeepSeek for free fallback
    "editorial_review": "google/gemini-2.5-flash-lite-preview-06-17",   # Fallback to Gemini 2.5
}
```

### Reliability Features
- 🔁 **Automatic retries** with intelligent backoff
- 🔄 **Model switching** on persistent failures
- 📊 **Detailed logging** of retry attempts and model usage
- ⚡ **Fast failover** to maintain pipeline flow
- 💾 **State preservation** across retry attempts

### Example Log Output
```
🤖 Using primary model for generate_article: deepseek/deepseek-chat-v3.1:free
❌ Model deepseek/deepseek-chat-v3.1:free failed (attempt 1): Rate limit exceeded
⏳ Waiting 2s before retry...
❌ Model deepseek/deepseek-chat-v3.1:free failed (attempt 2): Rate limit exceeded
⏳ Waiting 5s before retry...
✅ Model deepseek/deepseek-chat-v3.1:free responded successfully (attempt 3)
```

## 💰 Token Tracking

The system automatically tracks token usage for all providers with enhanced model information:

- **Per-request tracking**: Prompt, completion, and reasoning tokens
- **Provider metadata**: Which provider/model was used (including fallbacks)
- **Retry information**: Attempt counts and success rates
- **Stage breakdown**: Token usage by pipeline stage
- **Session summaries**: Complete usage reports

Example enhanced token report:
```json
{
  "session_summary": {
    "total_requests": 6,
    "total_tokens": 34363,
    "total_reasoning_tokens": 5791
  },
  "stage_breakdown": {
    "extract_prompts": {
      "requests": 5,
      "total_tokens": 23125,
      "provider": "openrouter",
      "model": "google/gemini-2.5-flash-lite-preview-06-17",
      "model_type": "primary"
    },
    "generate_wordpress_article": {
      "requests": 1,
      "total_tokens": 8450,
      "provider": "openrouter",
      "model": "deepseek/deepseek-chat-v3.1:free",
      "model_type": "primary",
      "attempt": 2
    }
  }
}
```

## 🔧 Advanced Configuration

### Adding New Providers

To add a new LLM provider:

1. **Add provider config** in `src/config.py`:
```python
LLM_PROVIDERS["new_provider"] = {
    "base_url": "https://api.newprovider.com",
    "api_key_env": "NEW_PROVIDER_API_KEY",
    "models": ["model-1", "model-2"],
    # Optional extra configuration
    "extra_headers": {"Custom-Header": "value"}
}
```

2. **Add API key** to `.env`:
```bash
NEW_PROVIDER_API_KEY=your_key_here
```

3. **Update model choices** in `LLM_MODELS` or use command line flags.

### Custom Client Configuration

The system automatically creates OpenAI-compatible clients for all providers. For providers requiring special handling, modify the `get_llm_client()` function in `src/llm_processing.py`.

## 🧪 Testing Your Setup

Test your configuration:

```python
from src.config import LLM_PROVIDERS, get_provider_for_model
from src.llm_processing import get_llm_client

# Test provider detection
print(get_provider_for_model("openai/gpt-4o-mini"))  # Should return "openrouter"

# Test client creation
client = get_llm_client("openai/gpt-4o-mini")
print("OpenRouter client created successfully!")
```

## ⚠️ Troubleshooting

### Common Issues

**1. API Key Not Found**
```
ValueError: API key not found for provider openrouter. Check OPENROUTER_API_KEY in .env
```
**Solution**: Add the required API key to your `.env` file.

**2. Model Not Recognized**
```
Model "custom-model" -> Provider: deepseek (fallback)
```
**Solution**: Add your model to the appropriate provider's `models` list in `LLM_PROVIDERS`.

**3. Retry Exhaustion**
```
🚨 All models failed for stage generate_article. Models tried: ['deepseek/deepseek-chat-v3.1:free', 'deepseek-reasoner']
```
**Solution**: Check network connectivity, API keys, or try different models.

**4. Free Model Rate Limits**
```
❌ Model deepseek/deepseek-chat-v3.1:free failed (attempt 1): Rate limit exceeded
```
**Solution**: System automatically retries. For frequent limits, consider paid alternatives.

**5. Fallback Model Issues**
```
💥 Model deepseek-reasoner exhausted all 3 attempts
```
**Solution**: Update fallback models in `FALLBACK_MODELS` config or check API keys.

### Debug Mode

Enable detailed logging by checking pipeline logs:
```bash
# Check recent LLM interactions
ls output/Your_Topic/*/llm_requests/
ls output/Your_Topic/*/llm_responses_raw/
```

## 🔗 Related Documentation

- **[Configuration Guide](configuration.md)** - Full configuration options
- **[Main README](README.md)** - Quick start and overview  
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Pipeline Flow](flow.md)** - Technical pipeline details

## 📈 Best Practices

1. **Start with 100% free defaults** - Use the all-free DeepSeek setup for maximum cost efficiency
2. **Monitor free model performance** - Check logs for rate limits and quality issues
3. **Strategic premium overrides** - Use premium models only when free models consistently fail
4. **Plan fallback costs** - Ensure fallback models have valid API keys and budget
5. **Monitor retry patterns** - Free models may hit rate limits more often
6. **Track actual costs** - Most operations should be FREE, monitor premium fallback usage
7. **Test retry scenarios** - Verify fallback activation works properly
8. **Consider peak usage times** - Free models may have higher latency during busy periods
9. **Quality vs Cost tradeoff** - Free models are surprisingly good for most tasks

---

*For technical implementation details, see the source code in `src/llm_processing.py` and `src/config.py`.*