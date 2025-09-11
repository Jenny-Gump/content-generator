import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import openai

from src.logger_config import logger
from src.token_tracker import TokenTracker
from src.config import LLM_MODELS, DEFAULT_MODEL, LLM_PROVIDERS, get_provider_for_model

# Загружаем переменные среды
load_dotenv()

# Словарь для кэширования клиентов
_clients_cache = {}

def get_llm_client(model_name: str) -> openai.OpenAI:
    """Get appropriate LLM client for the given model."""
    provider = get_provider_for_model(model_name)
    
    # Return cached client if available
    if provider in _clients_cache:
        return _clients_cache[provider]
    
    provider_config = LLM_PROVIDERS[provider]
    api_key = os.getenv(provider_config["api_key_env"])
    
    if not api_key:
        raise ValueError(f"API key not found for provider {provider}. Check {provider_config['api_key_env']} in .env")
    
    # Create client with provider-specific configuration
    client_kwargs = {
        "api_key": api_key,
        "base_url": provider_config["base_url"]
    }
    
    # Add extra headers for OpenRouter
    if "extra_headers" in provider_config:
        client_kwargs["default_headers"] = provider_config["extra_headers"]
    
    client = openai.OpenAI(**client_kwargs)
    
    # Cache the client
    _clients_cache[provider] = client
    
    return client

def save_llm_interaction(base_path: str, stage_name: str, messages: List[Dict], 
                         response: str, request_id: str = None, extra_params: Dict = None):
    """
    Сохраняет запрос и ответ LLM для отладки и анализа.
    
    Args:
        base_path: Базовый путь для сохранения (например, paths["extraction"])
        stage_name: Название этапа (например, "extract_prompts")
        messages: Сообщения, отправленные в LLM
        response: Сырой ответ от LLM
        request_id: ID запроса для множественных запросов (например, source_1)
        extra_params: Дополнительные параметры запроса
    """
    try:
        # Создаём подпапки для запросов и ответов
        requests_dir = os.path.join(base_path, "llm_requests")
        responses_dir = os.path.join(base_path, "llm_responses_raw")
        os.makedirs(requests_dir, exist_ok=True)
        os.makedirs(responses_dir, exist_ok=True)
        
        # Формируем имена файлов
        if request_id:
            request_filename = f"{request_id}_request.json"
            response_filename = f"{request_id}_response.txt"
        else:
            request_filename = f"{stage_name}_request.json"
            response_filename = f"{stage_name}_response.txt"
        
        # Подготавливаем данные запроса
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage_name,
            "model": extra_params.get("model", DEFAULT_MODEL) if extra_params else DEFAULT_MODEL,
            "messages": messages,
            "extra_params": extra_params or {}
        }
        
        # Сохраняем запрос
        request_path = os.path.join(requests_dir, request_filename)
        with open(request_path, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2, ensure_ascii=False)
        
        # Сохраняем ответ
        response_path = os.path.join(responses_dir, response_filename)
        with open(response_path, 'w', encoding='utf-8') as f:
            f.write(response)
        
        logger.info(f"Saved LLM interaction: {request_path} + {response_path}")
        
    except Exception as e:
        logger.error(f"Failed to save LLM interaction: {e}")

def _parse_json_from_response(response_content: str) -> Any:
    """
    Robustly parses JSON from LLM response, handling various formats:
    - Single objects: {...}
    - Arrays: [{...}, {...}]
    - Objects with data wrapper: {"data": [...]}
    - Malformed JSON with common errors
    - Escape character issues from LLM responses
    """
    response_content = response_content.strip()
    
    if not response_content:
        logger.error("Empty response content")
        return []
    
    # Attempt 1: Parse as-is
    try:
        parsed = json.loads(response_content)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return parsed.get("data", [parsed])  # If has data key, use it; otherwise wrap single object
        else:
            return []
    except json.JSONDecodeError:
        pass
    
    # Attempt 1.5: Fix escape character issues (common with Gemini responses)
    try:
        # Fix common Gemini escape patterns
        fixed_content = response_content
        
        # Remove code block wrappers if present
        if fixed_content.startswith('```json\n') and fixed_content.endswith('\n```'):
            fixed_content = fixed_content[8:-4].strip()
        elif fixed_content.startswith('```\n') and fixed_content.endswith('\n```'):
            fixed_content = fixed_content[4:-4].strip()
        
        # Fix escaped underscores in JSON keys (aggressive approach)
        fixed_content = fixed_content.replace('prompt\\_text', 'prompt_text')
        fixed_content = fixed_content.replace('expert\\_description', 'expert_description')
        fixed_content = fixed_content.replace('why\\_good', 'why_good')
        fixed_content = fixed_content.replace('how\\_to\\_improve', 'how_to_improve')
        
        # Fix any remaining backslash-underscore patterns
        fixed_content = re.sub(r'\\\\_', '_', fixed_content)
        
        parsed = json.loads(fixed_content)
        if isinstance(parsed, list):
            logger.info("Successfully parsed JSON after escape character fix")
            return parsed
        elif isinstance(parsed, dict):
            logger.info("Successfully parsed JSON after escape character fix")
            return parsed.get("data", [parsed])
        else:
            return []
    except json.JSONDecodeError as e:
        logger.debug(f"JSON fix attempt failed: {e}")
        pass
    
    # Attempt 2: If it looks like a single object, wrap it in an array
    if response_content.startswith('{') and response_content.endswith('}'):
        try:
            obj = json.loads(response_content)
            return [obj]
        except json.JSONDecodeError:
            pass
    
    # Attempt 3: Find JSON blocks in text using regex
    json_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
    matches = re.findall(json_pattern, response_content)
    if matches:
        parsed_objects = []
        for match in matches:
            try:
                obj = json.loads(match)
                parsed_objects.append(obj)
            except json.JSONDecodeError:
                continue
        if parsed_objects:
            return parsed_objects
    
    # Attempt 4: Try to fix common JSON errors
    fixed_content = response_content
    # Fix unescaped quotes in values
    fixed_content = re.sub(r'(?<=: ")(.*?)(?="[,}\]])', lambda m: m.group(1).replace('"', '\\"'), fixed_content)
    # Fix trailing commas
    fixed_content = re.sub(r',\s*([}\]])', r'\1', fixed_content)
    
    try:
        parsed = json.loads(fixed_content)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return parsed.get("data", [parsed])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse extracted JSON string: {e}")
        logger.error(f"String: {response_content[:1000]}")
        return []


def _load_and_prepare_messages(article_type: str, prompt_name: str, replacements: Dict[str, str]) -> List[Dict]:
    """Loads a prompt template, performs replacements, and splits into messages."""
    path = os.path.join("prompts", article_type, f"{prompt_name}.txt")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        for key, value in replacements.items():
            template = template.replace(f"{{{key}}}", str(value))

        lines = template.splitlines()
        system_content = ""
        user_content_lines = []

        if lines and lines[0].startswith("System:"):
            system_content = lines[0].replace("System:", "").strip()
            user_content_lines = lines[1:]
        else:
            user_content_lines = lines

        # Объединяем все строки кроме системной
        full_user_content = "\n".join(user_content_lines)
        
        # Заменяем маркер "User:" на пустоту, но сохраняем весь контент
        if "User:" in full_user_content:
            # Разделяем по "User:" и объединяем все части
            parts = full_user_content.split("User:")
            user_content = parts[0] + parts[1] if len(parts) == 2 else full_user_content
            user_content = user_content.strip()
        else:
            user_content = full_user_content

        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        
        return messages

    except FileNotFoundError:
        logger.error(f"Prompt file not found: {path}")
        raise

def extract_prompts_from_article(article_text: str, topic: str, base_path: str = None, 
                                 source_id: str = None, token_tracker: TokenTracker = None,
                                 model_name: str = None) -> List[Dict]:
    """Extracts structured prompt data from a single article text.
    
    Args:
        article_text: The text content to extract prompts from
        topic: The topic for context
        base_path: Path to save LLM interactions
        source_id: Identifier for the source
        token_tracker: Token usage tracker
        model_name: Override model name (uses config default if None)
    """
    logger.info("Extracting prompts from one article...")
    try:
        messages = _load_and_prepare_messages(
            "prompt_collection", 
            "01_extract", 
            {"topic": topic, "article_text": article_text}
        )
        # Use provided model or default from config
        model_to_use = model_name or LLM_MODELS.get("extract_prompts", DEFAULT_MODEL)
        client = get_llm_client(model_to_use)
        
        response = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=0.3,
            timeout=90
        )
        content = response.choices[0].message.content
        
        # Track token usage
        if token_tracker and response.usage:
            provider = get_provider_for_model(model_to_use)
            token_tracker.add_usage(
                stage="extract_prompts",
                usage=response.usage,
                source_id=source_id,
                extra_metadata={
                    "topic": topic, 
                    "model": model_to_use,
                    "provider": provider
                }
            )
        
        # Сохраняем запрос и ответ для отладки
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="extract_prompts",
                messages=messages,
                response=content,
                request_id=source_id or "single",
                extra_params={"response_format": "json_object", "topic": topic, "model": model_to_use}
            )
        
        parsed_json = _parse_json_from_response(content)
        if isinstance(parsed_json, list):
            return parsed_json
        elif isinstance(parsed_json, dict):
            return parsed_json.get("data", [parsed_json])  # If no data key, return object wrapped in array
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to extract prompts via API: {e}")
        return []


def generate_wordpress_article(prompts: List[Dict], topic: str, base_path: str = None, 
                              token_tracker: TokenTracker = None, model_name: str = None) -> Dict[str, Any]:
    """Generates a WordPress-ready article from collected prompts.
    
    Args:
        prompts: List of collected prompts to use for article generation
        topic: The topic for the article
        base_path: Path to save LLM interactions
        token_tracker: Token usage tracker
        model_name: Override model name (uses config default if None)
    """
    logger.info("Generating WordPress article from collected prompts...")
    try:
        messages = _load_and_prepare_messages(
            "prompt_collection",
            "01_generate_wordpress_article",
            {"topic": topic, "prompts_json": json.dumps(prompts, indent=2)}
        )
        # Use provided model or default from config
        model_to_use = model_name or LLM_MODELS.get("generate_article", DEFAULT_MODEL)
        client = get_llm_client(model_to_use)
        
        response_obj = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=0.3,
            timeout=300,  # Increased timeout to 5 minutes
            response_format={"type": "json_object"}  # Enforce JSON response
        )
        response = response_obj.choices[0].message.content
        
        # Track token usage
        if token_tracker and response_obj.usage:
            provider = get_provider_for_model(model_to_use)
            token_tracker.add_usage(
                stage="generate_wordpress_article",
                usage=response_obj.usage,
                extra_metadata={
                    "topic": topic, 
                    "input_prompts_count": len(prompts),
                    "model": model_to_use,
                    "provider": provider
                }
            )
        
        # Сохраняем запрос и ответ для отладки
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="generate_wordpress_article",
                messages=messages,
                response=response,
                extra_params={
                    "topic": topic, 
                    "input_prompts_count": len(prompts),
                    "purpose": "generate_wordpress_article",
                    "response_format": "json_object",
                    "model": model_to_use
                }
            )
        
        # Парсим JSON ответ с улучшенной обработкой
        try:
            # Попытка 1: стандартный парсинг
            wordpress_data = json.loads(response)
            logger.info(f"Successfully generated WordPress article: {wordpress_data.get('title', 'No title')}")
            return wordpress_data
        except json.JSONDecodeError as e:
            logger.warning(f"Standard JSON parsing failed: {e}")
            logger.info("Attempting enhanced JSON parsing...")
            
            # Попытка 2: улучшенный парсинг
            try:
                # Удаляем возможные проблемные символы в начале/конце
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                # Проверяем валидность JSON структуры
                if cleaned_response.startswith('{') and cleaned_response.count('{') > cleaned_response.count('}'):
                    # Незавершенный JSON - ищем последнюю валидную структуру
                    brace_count = 0
                    last_valid_pos = -1
                    
                    for i, char in enumerate(cleaned_response):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                last_valid_pos = i
                                break
                    
                    if last_valid_pos > 0:
                        cleaned_response = cleaned_response[:last_valid_pos + 1]
                
                wordpress_data = json.loads(cleaned_response)
                logger.info(f"Enhanced JSON parsing successful: {wordpress_data.get('title', 'No title')}")
                return wordpress_data
                
            except json.JSONDecodeError as e2:
                logger.error(f"Enhanced JSON parsing also failed: {e2}")
                logger.error(f"Response length: {len(response)} characters")
                logger.error(f"First 200 chars: {response[:200]}")
                logger.error(f"Last 200 chars: {response[-200:]}")
                
                # Fallback: return error structure
                return {
                    "title": f"Ошибка парсинга JSON: {topic}",
                    "content": f"<p>Не удалось распарсить ответ от LLM. Ответ получен полностью ({len(response)} символов), но содержит ошибки JSON форматирования.</p><details><summary>Сырой ответ (первые 2000 символов)</summary><pre>{response[:2000]}</pre></details>",
                    "excerpt": "Ошибка парсинга JSON ответа",
                    "slug": "json-parsing-error",
                    "categories": ["prompts"],
                    "_yoast_wpseo_title": "Ошибка парсинга JSON",
                    "_yoast_wpseo_metadesc": "Произошла ошибка при парсинге JSON ответа от LLM",
                    "image_caption": "Ошибка парсинга JSON",
                    "focus_keyword": "промпты"
                }
            
    except Exception as e:
        logger.error(f"Failed to generate WordPress article: {e}")
        return {
            "title": f"Критическая ошибка: {topic}",
            "content": f"<p>Критическая ошибка при генерации статьи: {str(e)}</p>",
            "excerpt": "Критическая ошибка генерации",
            "slug": "critical-error",
            "categories": ["prompts"],
            "_yoast_wpseo_title": "Критическая ошибка",
            "_yoast_wpseo_metadesc": "Критическая ошибка при генерации статьи",
            "image_caption": "Критическая ошибка",
            "focus_keyword": "ошибка"
        }
