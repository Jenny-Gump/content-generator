# LLM Debugging Guide

This guide explains how to use the enhanced LLM logging and debugging features, including the multi-provider system (September 2025) and original debugging features (January 2025).

## Overview

Every interaction with LLM providers (DeepSeek, OpenRouter) is automatically logged with full transparency:
- ✅ **Request logging**: Complete prompts, parameters, timestamps  
- ✅ **Response logging**: Raw LLM outputs before JSON parsing
- ✅ **Provider tracking**: Which provider/model was used for each request
- ✅ **Token monitoring**: Detailed usage breakdown including reasoning tokens
- ✅ **Error context**: Failed parsing attempts with detailed error messages
- ✅ **Metadata tracking**: Stage identification, request IDs, model settings

## Directory Structure

When you run the pipeline, LLM logs are saved alongside results:

```
output/Your_Topic/
├── token_usage_report.json       # 🆕 Multi-provider token analytics
├── 06_extracted_prompts/         # Stage: Extract prompts from articles
│   ├── all_prompts.json          # 📊 Final processed results
│   ├── llm_requests/             # 🔍 What was sent to LLM
│   │   ├── source_1_request.json # Request for first article (includes provider info)
│   │   ├── source_2_request.json # Request for second article  
│   │   └── ...
│   └── llm_responses_raw/        # 🔍 What LLM actually returned
│       ├── source_1_response.txt # Raw response from LLM provider
│       ├── source_2_response.txt
│       └── ...
└── 07_final_article/             # Stage: Generate WordPress article  
    ├── wordpress_data.json       # 📊 Complete WordPress data structure
    ├── article_content.html      # 📄 Generated article HTML
    ├── llm_requests/             # 🔍 Article generation requests
    │   └── generate_wordpress_article_request.json
    └── llm_responses_raw/        # 🔍 Article generation responses
        └── generate_wordpress_article_response.txt
```

## Request Log Format

Each `*_request.json` file contains:

```json
{
  "timestamp": "2025-09-11T10:30:45.123456",
  "stage": "extract_prompts",
  "model": "openai/gpt-4o-mini",
  "messages": [
    {
      "role": "system", 
      "content": "You are an expert Prompt Engineering researcher..."
    },
    {
      "role": "user",
      "content": "INPUT:\n---\n[full article text here]"
    }
  ],
  "extra_params": {
    "response_format": "json_object",
    "topic": "Best prompts for analysis", 
    "model": "openai/gpt-4o-mini"
  }
}
```

## Response Log Format

Each `*_response.txt` file contains the raw LLM output exactly as received:

```
{
    "prompt_text": "Analyze my Q4 sales data to identify which product categories had the strongest growth, what customer segments drove the most revenue, and where I should focus inventory investment for Q1.",
    "expert_description": "This prompt requests comprehensive Q4 sales analysis with specific focus areas and actionable insights for Q1 planning.",
    "why_good": "It provides clear, specific analysis requirements with defined business objectives and actionable output expectations.",
    "how_to_improve": "Add specific metrics to track (e.g., 'Calculate growth percentages' and 'Rank segments by revenue contribution') and specify desired output format."
}
```

## 🆕 Token Usage Analytics (September 2025)

The `token_usage_report.json` file provides detailed analytics for multi-provider token usage:

```json
{
  "session_summary": {
    "total_requests": 6,
    "total_prompt_tokens": 25420,
    "total_completion_tokens": 8943,
    "total_tokens": 34363,
    "total_reasoning_tokens": 5791,
    "session_duration_minutes": 8.5
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
  },
  "detailed_breakdown": [
    {
      "timestamp": "2025-09-11T10:30:45.123456",
      "stage": "extract_prompts",
      "model": "deepseek-reasoner",
      "provider": "deepseek",
      "prompt_tokens": 2768,
      "completion_tokens": 2041,
      "reasoning_tokens": 1390,
      "total_tokens": 4809
    }
  ]
}
```

**Key metrics tracked:**
- **Total tokens**: Across all requests and providers
- **Reasoning tokens**: DeepSeek-specific reasoning token usage
- **Provider breakdown**: Usage by DeepSeek vs OpenRouter
- **Stage analytics**: Token consumption by pipeline stage
- **Performance data**: Session duration and average tokens per request

## Common Debugging Scenarios

### 1. JSON Parsing Failures

**Problem**: Log shows `Failed to parse extracted JSON string: Extra data: line 5 column 4`

**Solution**:
1. Check the raw response file: `llm_responses_raw/source_X_response.txt`
2. Look for malformed JSON (missing quotes, extra commas, unescaped characters)
3. The robust parser should handle most issues automatically, but you can see what went wrong

**Example debugging**:
```bash
# Check what LLM actually returned
cat "output/Best_prompts_for_analysis/06_extracted_prompts/llm_responses_raw/source_1_response.txt"

# Compare with the request that was sent  
cat "output/Best_prompts_for_analysis/06_extracted_prompts/llm_requests/source_1_request.json"
```

### 2. LLM Not Following Instructions

**Problem**: LLM returns wrong format or ignores instructions

**Solution**:
1. Examine the exact prompt sent in `*_request.json`
2. Check if the prompt is clear and has good examples
3. Review raw response to understand LLM's interpretation
4. Modify prompts in `prompts/prompt_collection/` if needed

### 3. Empty or Invalid Results

**Problem**: Final results are empty or contain "Error generating example"

**Solution**:
1. Check raw responses for actual LLM errors vs parsing failures
2. Look for API timeouts or rate limiting in responses  
3. Verify request parameters (max_tokens, model settings)

### 4. Inconsistent LLM Behavior

**Problem**: Same input produces different outputs

**Solution**:
1. Compare multiple request/response pairs for patterns
2. Check if prompts have non-deterministic elements
3. Review temperature and other model parameters

## Reproducing Issues

To reproduce a specific LLM interaction:

1. **Find the request file**: `llm_requests/problematic_request.json`
2. **Extract the prompt**: Copy `messages` array from the JSON
3. **Test manually**: Send the exact same prompt to DeepSeek API
4. **Compare responses**: See if the issue is consistent

## Optimizing Prompts

Use the logs to improve prompt engineering:

1. **Analyze successful patterns**: Look at requests that produced good results
2. **Identify failure modes**: Find common errors in raw responses
3. **A/B test prompts**: Modify prompts and compare results using logs
4. **Fine-tune examples**: Add better examples based on actual LLM confusion

## Performance Analysis

Track LLM performance over time:

```bash
# Count successful vs failed requests
grep -r "timestamp" output/*/llm_requests/ | wc -l  # Total requests
grep -r "Error" logs/operations.jsonl | wc -l      # Failed requests

# Find slowest requests (check timestamps)
find output/ -name "*_request.json" -exec grep -l "timestamp.*2025-01-15T10:3[0-5]" {} \;
```

## Integration with Main Logs

LLM logs complement the main application logs:
- **Application logs**: `logs/operations.jsonl` - High-level pipeline status
- **LLM logs**: `output/*/llm_*` - Detailed LLM interactions  
- **Pipeline logs**: `pipeline.log` - Step-by-step execution

## Best Practices

1. **Regular cleanup**: LLM logs can be large, archive old runs periodically
2. **Privacy**: Be careful with sensitive data in prompts when sharing logs
3. **Version control**: Don't commit LLM response files to git (add to .gitignore)
4. **Monitoring**: Watch for increasing error rates in LLM interactions
5. **Documentation**: When you find good prompts, document them for reuse

## Troubleshooting Quick Reference

| Problem | Check Files | Look For |
|---------|-------------|----------|
| JSON Parse Error | `*_response.txt` | Malformed JSON, extra text |
| Empty Results | `*_request.json` + `*_response.txt` | API errors, wrong prompts |
| Wrong Format | `*_response.txt` | LLM not following instructions |
| Slow Performance | Request timestamps | Long delay patterns |
| API Errors | `*_response.txt` | Error messages from DeepSeek |

This logging system provides complete transparency into LLM behavior, making it much easier to debug issues and optimize the content generation pipeline.