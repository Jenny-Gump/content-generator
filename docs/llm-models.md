# LLM Models & Providers Guide

This guide covers the flexible multi-provider LLM system in the Content Generator pipeline. The system supports multiple providers and allows easy switching between models for different tasks.

## 🎛️ Multi-Provider Architecture

The Content Generator supports multiple LLM providers through a unified interface:

- **OpenRouter**: Primary provider - gateway to Google Gemini 2.5 (65K tokens), OpenAI models (GPT-4o, GPT-4o-mini, etc.)
- **DeepSeek**: Alternative provider with reasoning capabilities
- **Extensible**: Easy to add new providers

## 📋 Configuration Overview

### Default Configuration (`src/config.py`)

```python
# Default models for each pipeline stage
LLM_MODELS = {
    "extract_prompts": "google/gemini-2.5-flash-lite-preview-06-17",      # Model for prompt extraction
    "generate_article": "google/gemini-2.5-flash-lite-preview-06-17",    # Model for article generation
}

# Fallback model
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
            "openai/gpt-3.5-turbo"
        ]
    }
}
```

## 🔑 API Keys Setup

Add the following keys to your `.env` file:

```bash
# Required for Google Gemini models via OpenRouter (PRIMARY)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx

# Required for Firecrawl search/scraping
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional - for alternative models
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note**: Only the keys for providers you plan to use are required.

## 🚀 Command Line Usage

### Basic Usage

```bash
# Use default models (Google Gemini 2.5 for all tasks)
python main.py "Your topic"
```

### Model Overrides

```bash
# Use OpenAI GPT-4o-mini for article generation only
python main.py "Your topic" --generate-model "openai/gpt-4o-mini"

# Use different models for each stage
python main.py "Your topic" --extract-model "deepseek-chat" --generate-model "openai/gpt-4o"

# See all available options
python main.py --help
```

### Available Flags

- `--extract-model MODEL` - Override model for prompt extraction
- `--generate-model MODEL` - Override model for article generation  
- `--provider {deepseek,openrouter}` - Specify provider preference

## 📖 Available Models

### DeepSeek Models

| Model | Description | Best For |
|-------|-------------|----------|
| `deepseek-reasoner` | Most capable with reasoning | Complex tasks, default choice |
| `deepseek-chat` | Faster conversational model | Quick extraction, speed-critical tasks |

### Google Gemini Models (via OpenRouter) ⭐ **PRIMARY**

| Model | Max Tokens | Description | Best For |
|-------|------------|-------------|----------|
| `google/gemini-2.5-flash-lite-preview-06-17` | **65,535** | Ultra-fast, high-capacity model | **Default choice - no truncation** |
| `google/gemini-2.0-flash-001` | 8,192 | Fast multimodal model | ⚠️ Limited for long articles |

### OpenAI Models (via OpenRouter)

| Model | Max Tokens | Description | Best For |
|-------|------------|-------------|----------|
| `openai/gpt-4o` | 16,384 | Latest GPT-4 Omni | Highest quality generation |
| `openai/gpt-4o-mini` | 16,384 | Smaller, faster GPT-4 Omni | Balanced quality/speed |
| `openai/gpt-4-turbo` | 4,096 | GPT-4 Turbo | High-quality, fast processing |
| `openai/gpt-3.5-turbo` | 4,096 | Fast and cost-effective | Budget-conscious tasks |

## 🎯 Configuration Examples

### Example 1: Default Gemini 2.5 Setup ⭐ **RECOMMENDED**
```python
LLM_MODELS = {
    "extract_prompts": "google/gemini-2.5-flash-lite-preview-06-17",   # High capacity
    "generate_article": "google/gemini-2.5-flash-lite-preview-06-17",  # No truncation issues
}
```

### Example 2: Mixed High-Performance Setup  
```python
LLM_MODELS = {
    "extract_prompts": "deepseek-reasoner",     # Thorough extraction
    "generate_article": "google/gemini-2.5-flash-lite-preview-06-17",  # Large output capacity
}
```

### Example 3: Alternative Models Setup
```python
LLM_MODELS = {
    "extract_prompts": "openai/gpt-4o-mini",    # Fast OpenAI for extraction
    "generate_article": "openai/gpt-4o",       # Premium OpenAI for generation
}
```

### Example 4: Budget-Conscious Setup
```python
LLM_MODELS = {
    "extract_prompts": "deepseek-chat",         # Free, fast extraction
    "generate_article": "openai/gpt-3.5-turbo", # Low-cost generation
}
```

## 💰 Token Tracking

The system automatically tracks token usage for all providers:

- **Per-request tracking**: Prompt, completion, and reasoning tokens
- **Provider metadata**: Which provider/model was used
- **Stage breakdown**: Token usage by pipeline stage
- **Session summaries**: Complete usage reports

Example token report:
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
      "provider": "deepseek"
    },
    "generate_wordpress_article": {
      "requests": 1,
      "total_tokens": 11238,
      "provider": "openrouter"
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

**3. Network/API Errors**
Check the logs for detailed error messages. Common issues:
- Rate limiting (try different model or wait)
- Invalid API key (regenerate key)
- Network connectivity (check internet connection)

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

1. **Start with defaults** - Use `deepseek-reasoner` for initial testing
2. **Experiment gradually** - Try one model override at a time  
3. **Monitor costs** - Check token usage reports for optimization
4. **Match task complexity** - Use simpler models for extraction, powerful ones for generation
5. **Consider latency** - OpenAI models via OpenRouter may have higher latency
6. **Test thoroughly** - Always validate output quality when switching models

---

*For technical implementation details, see the source code in `src/llm_processing.py` and `src/config.py`.*