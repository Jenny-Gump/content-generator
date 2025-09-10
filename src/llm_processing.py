import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import openai

from src.logger_config import logger

# Загружаем переменные среды
load_dotenv()

DEEPSEEK_MODEL = "deepseek-reasoner" 
# Используем OpenAI-совместимый клиент как в AI News проекте
client = openai.OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

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
            "model": DEEPSEEK_MODEL,
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
                                 source_id: str = None) -> List[Dict]:
    """Extracts structured prompt data from a single article text."""
    logger.info("Extracting prompts from one article...")
    try:
        messages = _load_and_prepare_messages(
            "prompt_collection", 
            "01_extract", 
            {"topic": topic, "article_text": article_text}
        )
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.3,
            timeout=90
        )
        content = response.choices[0].message.content
        
        # Сохраняем запрос и ответ для отладки
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="extract_prompts",
                messages=messages,
                response=content,
                request_id=source_id or "single",
                extra_params={"response_format": "json_object", "topic": topic}
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

def rank_and_select_prompts(prompts: List[Dict], topic: str, base_path: str = None) -> List[Dict]:
    """Ranks and selects the best prompts from a list."""
    logger.info(f"Ranking and selecting from {len(prompts)} prompts...")
    try:
        messages = _load_and_prepare_messages(
            "prompt_collection",
            "02_rank",
            {"topic": topic, "prompts_json": json.dumps(prompts, indent=2)}
        )
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.3,
            timeout=90
        )
        content = response.choices[0].message.content
        
        # Сохраняем запрос и ответ для отладки
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="rank_prompts",
                messages=messages,
                response=content,
                extra_params={
                    "topic": topic, 
                    "input_prompts_count": len(prompts)
                }
            )
        
        parsed_json = _parse_json_from_response(content)
        if isinstance(parsed_json, list):
            return parsed_json
        elif isinstance(parsed_json, dict):
            return parsed_json.get("data", [parsed_json])  # If no data key, return object wrapped in array
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to rank prompts via API: {e}")
        return []

def generate_expert_content_for_prompt(prompt: Dict, base_path: str = None, 
                                      prompt_index: int = None) -> Dict:
    """Generates an example output and expert commentary for a single prompt."""
    prompt_text = prompt.get("prompt_text", "")
    logger.info(f"Generating expert content for prompt: '{prompt_text[:50]}...'")
    
    # Формируем ID для запросов (если есть индекс)
    request_id_base = f"prompt_{prompt_index}" if prompt_index is not None else "single"
    
    try:
        # Первый запрос: генерация примера выполнения с полным контекстом
        example_context = f"""PROMPT TO DEMONSTRATE:
{prompt_text}

CONTEXT FOR BETTER EXAMPLE:
- Purpose: {prompt.get('expert_description', 'Not specified')}
- Why it's effective: {prompt.get('why_good', 'Not specified')}

Generate a realistic, high-quality example of what this prompt would produce when executed. Show the actual output/result, not meta-commentary about the prompt."""
        
        example_messages = [{"role": "user", "content": example_context}]
        example_response_obj = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=example_messages,
            max_tokens=200,
            temperature=0.3,
            timeout=90
        )
        example_response = example_response_obj.choices[0].message.content
        prompt["example_output"] = example_response
        
        # Сохраняем первый запрос
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="generate_example",
                messages=example_messages,
                response=example_response,
                request_id=f"{request_id_base}_example",
                extra_params={"max_tokens": 200, "purpose": "generate_example_output"}
            )

        # Второй запрос: генерация экспертного комментария с существующим анализом
        commentary_messages = _load_and_prepare_messages(
            "prompt_collection",
            "03_generate_commentary",
            {
                "prompt_text": prompt_text,
                "expert_description": prompt.get('expert_description', 'Not provided'),
                "why_good": prompt.get('why_good', 'Not provided'), 
                "how_to_improve": prompt.get('how_to_improve', 'Not provided'),
                "scoring_data": f"Total Score: {prompt.get('total_score', 'N/A')}, Rank: {prompt.get('rank', 'N/A')}" if 'total_score' in prompt else 'Not available'
            }
        )
        commentary_response_obj = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=commentary_messages,
            max_tokens=600,
            temperature=0.3,
            timeout=90
        )
        commentary_response = commentary_response_obj.choices[0].message.content
        prompt["expert_commentary"] = commentary_response
        
        # Сохраняем второй запрос
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="generate_commentary",
                messages=commentary_messages,
                response=commentary_response,
                request_id=f"{request_id_base}_commentary",
                extra_params={"max_tokens": 600, "purpose": "generate_expert_commentary"}
            )
        
    except Exception as e:
        logger.error(f"Failed to generate expert content for prompt '{prompt_text[:50]}...': {e}")
        prompt["example_output"] = "Error generating example."
        prompt["expert_commentary"] = "Error generating commentary."
    
    return prompt

def assemble_final_article(enriched_prompts: List[Dict], topic: str, base_path: str = None) -> str:
    """Assembles the final article from the enriched prompts."""
    logger.info("Assembling the final article...")
    try:
        messages = _load_and_prepare_messages(
            "prompt_collection",
            "04_assemble_article",
            {"topic": topic, "enriched_prompts_json": json.dumps(enriched_prompts, indent=2)}
        )
        response_obj = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.3,
            timeout=90
        )
        response = response_obj.choices[0].message.content
        
        # Сохраняем запрос и ответ для отладки
        if base_path:
            save_llm_interaction(
                base_path=base_path,
                stage_name="assemble_article",
                messages=messages,
                response=response,
                extra_params={
                    "topic": topic, 
                    "input_prompts_count": len(enriched_prompts),
                    "purpose": "assemble_final_article"
                }
            )
        
        return response
    except Exception as e:
        logger.error(f"Failed to assemble final article: {e}")
        return "Error: Could not generate the final article."
