# LLM Debugging Guide

This guide explains how to use the enhanced LLM logging features added in January 2025 to debug and optimize the content generation pipeline.

## Overview

Every interaction with the DeepSeek API is automatically logged with full transparency:
- ✅ **Request logging**: Complete prompts, parameters, timestamps
- ✅ **Response logging**: Raw LLM outputs before JSON parsing  
- ✅ **Error context**: Failed parsing attempts with detailed error messages
- ✅ **Metadata tracking**: Stage identification, request IDs, model settings

## Directory Structure

When you run the pipeline, LLM logs are saved alongside results:

```
output/Your_Topic/
├── 06_extracted_prompts/           # Stage 7: Extract prompts from articles
│   ├── all_prompts.json           # 📊 Final processed results
│   ├── llm_requests/              # 🔍 What was sent to LLM
│   │   ├── source_1_request.json  # Request for first article
│   │   ├── source_2_request.json  # Request for second article  
│   │   └── ...
│   └── llm_responses_raw/         # 🔍 What LLM actually returned
│       ├── source_1_response.txt  # Raw response from LLM
│       ├── source_2_response.txt
│       └── ...
├── 07_ranked_prompts/             # Stage 8: Rank and select prompts
│   ├── best_prompts.json          # 📊 Final ranked results
│   ├── llm_requests/
│   │   └── rank_prompts_request.json
│   └── llm_responses_raw/
│       └── rank_prompts_response.txt
├── 08_enriched_prompts/           # Stage 9: Generate examples & commentary
│   ├── enriched_prompts.json      # 📊 Final enriched results
│   ├── llm_requests/              # 🔍 2 requests per prompt
│   │   ├── prompt_1_example_request.json
│   │   ├── prompt_1_commentary_request.json
│   │   ├── prompt_2_example_request.json
│   │   └── ...
│   └── llm_responses_raw/
│       ├── prompt_1_example_response.txt
│       ├── prompt_1_commentary_response.txt
│       └── ...
└── 09_final_article/             # Stage 10: Assemble final article
    ├── final_article.md           # 📊 Final article
    ├── llm_requests/
    │   └── assemble_article_request.json
    └── llm_responses_raw/
        └── assemble_article_response.txt
```

## Request Log Format

Each `*_request.json` file contains:

```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
  "stage": "extract_prompts",
  "model": "deepseek-reasoner",
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
    "max_tokens": 200
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