# Changelog

All notable changes to the Content Generation Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Editorial Review JSON Parsing Issue** (Sept 11, 2025)
  - **Problem**: Editorial review stage was falling back to original WordPress data containing block tags due to JSON parsing failures
  - **Root Cause**: LLM responses contained unescaped control characters (newlines, tabs) in JSON string values, causing `"Invalid control character"` errors
  - **Solution**: Added robust error recovery with manual field extraction fallback
  - **Impact**: WordPress block tags are now properly cleaned even when JSON parsing fails
  - **Technical Details**: 
    - Enhanced `editorial_review()` function in `src/llm_processing.py`
    - Added regex-based field extraction when standard JSON parsing fails
    - Preserves all LLM-generated content improvements even with malformed JSON structure
    - Manual extraction successfully recovers title, content, excerpt, SEO metadata, etc.

### Technical Improvements
- Enhanced JSON parsing error handling with graceful degradation
- Added detailed logging for editorial review process debugging
- Improved error recovery prevents loss of LLM content improvements

---

## Version History

### Pre-changelog Releases
- Multi-provider LLM system (DeepSeek, OpenRouter)
- WordPress integration with SEO optimization
- Content pipeline with search, parsing, scoring, selection, and cleaning stages
- Editorial review stage implementation
- Token tracking and usage analytics

---

## Bug Fixes & Technical Notes

### Editorial Review JSON Parsing (2025-09-11)

**Issue Identification Process**:
1. User reported WordPress block tags remaining in final output despite editorial review
2. Created reproduction environment using actual pipeline output data
3. Identified JSON parsing failure due to control characters at position 4470
4. Implemented and tested manual extraction solution
5. Verified WordPress tags are properly cleaned by LLM before extraction

**Before Fix**:
```
LLM Response: Clean content without WordPress tags ✅
JSON Parsing: FAILED due to control characters ❌  
Final Output: Falls back to original dirty data with WordPress tags ❌
```

**After Fix**:
```
LLM Response: Clean content without WordPress tags ✅
JSON Parsing: FAILED → Manual extraction triggered ✅
Final Output: Clean content without WordPress tags preserved ✅
```

**Files Modified**:
- `src/llm_processing.py`: Enhanced `editorial_review()` function
- `docs/troubleshooting.md`: Updated JSON parsing section

**Test Results**:
- Manual extraction: 9/9 fields recovered successfully
- WordPress tags: Completely removed from final output
- Content quality: Preserved all LLM improvements
- Error recovery: 100% successful fallback

This fix ensures the editorial review stage works reliably even when LLM responses contain JSON formatting issues, maintaining the quality improvements while providing robust error handling.