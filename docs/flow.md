# Pipeline Flow Description

This document provides a detailed, step-by-step breakdown of the content generation pipeline.

## 🔍 LLM Debugging Features (NEW)

Starting from January 2025, all LLM interactions are automatically logged for debugging:
- **Full Request Logging**: Every prompt sent to DeepSeek API
- **Raw Response Logging**: Unprocessed LLM outputs before JSON parsing
- **Error Context**: Failed parsing attempts with detailed error messages
- **Metadata Tracking**: Timestamps, model parameters, and request IDs

**Benefits**:
- ✅ Debug JSON parsing failures by examining raw responses
- ✅ Understand LLM behavior by reviewing actual prompts sent
- ✅ Reproduce specific errors by re-running exact same requests
- ✅ Optimize prompts based on actual LLM outputs

### Этап 1: Запрос (The Request)

**📥 ВХОДНЫЕ ДАННЫЕ:** 
- Командная строка: `python main.py "тема"`
- Аргумент topic (строка)

**🎯 ЦЕЛЬ:** Получить исходную тему для всего пайплайна

**⚙️ ФУНКЦИИ:**
- `main.py` → `argparse` парсинг аргументов
- Валидация входной строки (не пустая)
- Создание базовой структуры папок `output/{тема}/`

**🔄 ПРОЦЕСС:** 
1. Пользователь вводит тему: `"Best prompts for data analysis in 2025"`
2. Система создает slug из темы для имен папок
3. Инициализируется структура директорий для артефактов

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
- `topic: str` - исходная тема
- `topic_slug: str` - нормализованное имя для папок
- Созданы папки: `output/{topic_slug}/01_search/...`

---

### Этап 2: Поиск (Search)

**📥 ВХОДНЫЕ ДАННЫЕ:**
- `topic: str` - тема для поиска
- `FIRECRAWL_API_KEY` - API ключ из .env
- `search_limit: int = 20` - количество результатов

**🎯 ЦЕЛЬ:** Найти максимально широкий, но релевантный список URL-адресов по теме

**⚙️ ФУНКЦИИ:**
- `src/firecrawl_service.py` → `search_urls(topic)`
- Firecrawl Search API (`/v2/search`) запрос
- Обработка ошибок API и таймаутов

**🔄 ПРОЦЕСС:**
1. Формируется поисковый запрос без кавычек для широкого охвата
2. POST запрос к `https://api.firecrawl.dev/v2/search`
3. API возвращает топ-20 результатов из поисковой выдачи Google
4. Первичная валидация URL (исключение битых ссылок)

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Best Data Analysis Prompts 2025",
    "description": "Complete guide to...",
    "favicon": "https://example.com/favicon.ico"
  }
]
```
**📁 Артефакт:** `output/{тема}/01_search/01_search_results.json`

---

### Этап 3: Парсинг (Parsing)

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Список URL из этапа 2 (20 ссылок)
- `filters/blocked_domains.json` - черный список доменов
- `MIN_CONTENT_LENGTH = 1000` - минимальная длина статьи

**🎯 ЦЕЛЬ:** Извлечь основной контент с каждого URL и отсеять неподходящие статьи

**⚙️ ФУНКЦИИ:**
- `src/processing.py` → `filter_urls()` - фильтрация по черному списку
- `src/firecrawl_service.py` → `scrape_url()` - конкурентный парсинг
- Firecrawl Scrape API (`/v2/scrape`) с `onlyMainContent: true`
- Валидация длины контента

**🔄 ПРОЦЕСС:**
1. **Предварительная фильтрация:** Проверка каждого URL по `blocked_domains.json`
2. **Конкурентное извлечение:** Параллельные запросы к Firecrawl Scrape API
3. **Валидация контента:** Проверка минимальной длины (1000+ символов)
4. **Очистка данных:** Удаление статей с пустым или коротким контентом

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Complete Guide to Data Analysis",
    "content": "# Introduction\n\nData analysis has become..." // Markdown
  }
]
```
**📁 Артефакты:**
- `01_clean_urls.json` - URL после фильтрации
- `02_scraped_data.json` - сырые данные от Firecrawl  
- `03_valid_sources.json` - валидированные источники

---

### Этап 4: Оценка (Scoring)

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Валидные источники из этапа 3
- `filters/trusted_sources.json` - белый список доменов
- `topic` - ключевые слова для релевантности
- Веса из `src/config.py`: TRUST_WEIGHT, RELEVANCE_WEIGHT, DEPTH_WEIGHT

**🎯 ЦЕЛЬ:** Присвоить каждому источнику объективную трехмерную оценку качества

**⚙️ ФУНКЦИИ:**
- `src/processing.py` → `calculate_trust_score()` - проверка доверенных доменов
- `src/processing.py` → `calculate_relevance_score()` - анализ ключевых слов
- `src/processing.py` → `calculate_depth_score()` - оценка глубины контента
- Токенизация и анализ текста

**🔄 ПРОЦЕСС:**
1. **Трастовость:** Проверка домена по `trusted_sources.json` → (1.0-2.5)
2. **Релевантность:** Подсчет вхождений ключевых слов:
   - В заголовке: вес × 3
   - В тексте: стандартный вес
3. **Глубина:** Длина статьи в символах → нормализация к (0-1)
4. **Агрегация:** Сохранение всех метрик для следующего этапа

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Complete Guide",
    "content": "...",
    "trust_score": 2.0,      // 1.0-2.5
    "relevance_score": 0.8,  // 0.0-1.0
    "depth_score": 0.9       // 0.0-1.0
  }
]
```
**📁 Артефакт:** `output/{тема}/03_scoring/scored_sources.json`

---

### Этап 5: Отбор (Selection)

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Оцененные источники с метриками (trust, relevance, depth)
- Веса из config: `TRUST_WEIGHT=0.5`, `RELEVANCE_WEIGHT=0.3`, `DEPTH_WEIGHT=0.2`
- `TOP_SOURCES_COUNT = 5` - количество финалистов

**🎯 ЦЕЛЬ:** Выбрать 5 "чемпионов" - лучших источников для LLM анализа

**⚙️ ФУНКЦИИ:**
- `src/processing.py` → `normalize_scores()` - приведение к единой шкале
- `src/processing.py` → `calculate_final_score()` - взвешенная формула
- `src/processing.py` → `select_top_sources()` - отбор финалистов
- Сортировка по финальному баллу

**🔄 ПРОЦЕСС:**
1. **Нормализация:** Все оценки приводятся к шкале (0-1)
2. **Взвешенная формула:** 
   ```python
   Final_Score = (trust * 0.5) + (relevance * 0.3) + (depth * 0.2)
   ```
3. **Сортировка:** Весь список по `Final_Score` (убывание)
4. **Отбор топ-5:** Берутся лучшие источники для LLM этапов

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Best Guide",
    "content": "...",
    "trust_score": 2.0,
    "relevance_score": 0.9,
    "depth_score": 0.8,
    "final_score": 1.57,    // Взвешенная сумма
    "rank": 1               // Позиция в рейтинге
  }
]
```
**📁 Артефакт:** `output/{тема}/04_selection/top_5_sources.json`

---

### Этап 6: Очистка (Cleaning)

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Топ-5 источников с "грязным" Markdown контентом
- Паттерны очистки в `src/processing.py`
- Список нежелательных элементов (навигация, реклама)

**🎯 ЦЕЛЬ:** Удалить семантический "мусор" и подготовить чистый текст для LLM

**⚙️ ФУНКЦИИ:**
- `src/processing.py` → `clean_content()` - основная очистка
- `remove_navigation_elements()` - удаление навигации
- `clean_markdown_artifacts()` - очистка разметки
- `normalize_whitespace()` - нормализация пробелов
- Регулярные выражения для паттернов мусора

**🔄 ПРОЦЕСС:**
1. **Удаление навигации:** Меню, breadcrumbs, "Related articles"
2. **Очистка рекламы:** Banner текст, партнерские ссылки
3. **Markdown артефакты:** Битая разметка, лишние символы
4. **Нормализация:** Множественные переносы → одинарные
5. **Валидация:** Проверка что основной контент сохранен

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Best Guide",
    "cleaned_content": "# Data Analysis Prompts\n\nHere are the most effective..." // Чистый Markdown
  }
]
```
**📁 Артефакты:**
- `final_cleaned_sources.json` - JSON со всеми источниками
- `source_1.md`, `source_2.md`... - отдельные файлы статей

---

### Этап 7: Извлечение промптов (Prompt Extraction) 🤖

**📥 ВХОДНЫЕ ДАННЫЕ:**
- 5 очищенных статей (`cleaned_content`)
- Промпт-шаблон `prompts/prompt_collection/01_extract.txt`
- `topic` для контекстуализации извлечения
- DeepSeek R1 Reasoner API credentials

**🎯 ЦЕЛЬ:** Извлечь структурированные промпты из контента с помощью Chain of Thought reasoning

**⚙️ ФУНКЦИИ:**
- `src/llm_processing.py` → `extract_prompts_from_article()` - главная функция
- `_load_and_prepare_messages()` - подготовка промпт-шаблона
- `client.chat_completion()` - вызов DeepSeek R1 API
- `_parse_json_from_response()` - робастный JSON парсинг (4 стратегии)
- `save_llm_interaction()` - 🆕 логирование запросов/ответов

**🔄 ПРОЦЕСС:**
1. **Для каждой статьи (5 итераций):**
   - Загружается шаблон `01_extract.txt`
   - Подставляется `{topic}` и `{article_text}`
   - Отправляется к DeepSeek R1 с `response_format: json_object`
2. **LLM анализ:** Chain of Thought извлечение промптов
3. **Парсинг ответа:** 4-этапная стратегия обработки JSON
4. **🆕 Логирование:** Сохранение запроса/ответа для отладки

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "prompt_text": "Analyze this dataset and provide insights on...",
    "expert_description": "Advanced data analysis prompt for...",
    "why_good": "Effective because it provides clear structure...",
    "how_to_improve": "Could be enhanced by adding specific metrics..."
  }
]
```
**📁 Артефакты:**
- `all_prompts.json` - агрегированные промпты из всех источников
- 🆕 `llm_requests/source_1_request.json` - что послали в LLM
- 🆕 `llm_responses_raw/source_1_response.txt` - сырой ответ от LLM

---

### Этап 8: Ранжирование промптов (Prompt Ranking) 🤖

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Все извлеченные промпты из этапа 7 (обычно 15-30 промптов)
- Промпт-шаблон `prompts/prompt_collection/02_rank.txt`
- `topic` для контекстуальной оценки релевантности
- 6 критериев оценки (по шкале 1-5 каждый)

**🎯 ЦЕЛЬ:** Ранжировать промпты по 6 критериям и отобрать топ-5-7 лучших

**⚙️ ФУНКЦИИ:**
- `src/llm_processing.py` → `rank_and_select_prompts()` - главная функция
- DeepSeek R1 Reasoner для многокритериального анализа
- Критерии: clarity, actionability, completeness, effectiveness, reusability, analysis_quality
- `_parse_json_from_response()` - обработка структурированного JSON

**🔄 ПРОЦЕСС:**
1. **Агрегация:** Все промпты объединяются в единый список
2. **LLM оценка:** DeepSeek R1 анализирует каждый промпт по 6 критериям:
   - Clarity & Specificity (1-5)
   - Actionability (1-5)  
   - Completeness (1-5)
   - Effectiveness Evidence (1-5)
   - Reusability (1-5)
   - Quality of Analysis (1-5)
3. **Итоговый скор:** Сумма всех оценок (макс. 30 баллов)
4. **Отбор финалистов:** Только промпты с total_score ≥ 20

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "data": [
    {
      "prompt_text": "Analyze this dataset...",
      "expert_description": "Advanced analysis prompt",
      "why_good": "Clear structure and examples",
      "how_to_improve": "Add specific metrics",
      "scores": {
        "clarity_specificity": 4,
        "actionability": 5,
        "completeness": 4,
        "effectiveness_evidence": 5,
        "reusability": 4,
        "quality_of_analysis": 4
      },
      "total_score": 26,
      "rank": 1
    }
  ]
}
```
**📁 Артефакты:**
- `best_prompts.json` - топ промпты с полными оценками
- 🆕 `llm_requests/rank_prompts_request.json` - запрос с всеми промптами
- 🆕 `llm_responses_raw/rank_prompts_response.txt` - полный ответ LLM

---

### Этап 9: Обогащение контента (Content Enrichment) 🤖

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Топ-промпты с рейтингами из этапа 8 (5-7 штук)
- Промпт-шаблон `prompts/prompt_collection/03_generate_commentary.txt`
- Существующий анализ: `expert_description`, `why_good`, `how_to_improve`, `scores`
- Token limits: 200 для примеров, 600 для комментариев

**🎯 ЦЕЛЬ:** Обогатить каждый промпт практическим примером и продвинутым экспертным анализом

**⚙️ ФУНКЦИИ:**
- `src/llm_processing.py` → `generate_expert_content_for_prompt()` - главная функция
- **2 LLM вызова на промпт:**
  1. Генерация примера выполнения (max_tokens=200)
  2. Экспертный комментарий (max_tokens=600) 
- Построение на существующем анализе (не дублирование!)

**🔄 ПРОЦЕСС:**
**Для каждого промпта (2 запроса):**

1. **Запрос 1 - Генерация примера:**
   ```
   PROMPT TO DEMONSTRATE: {prompt_text}
   CONTEXT: {expert_description + why_good}
   → Показать реалистичный результат выполнения
   ```

2. **Запрос 2 - Экспертный комментарий:**
   - Использует шаблон `03_generate_commentary.txt`
   - СТРОИТСЯ НА существующем анализе
   - 4 секции: Effectiveness Analysis, Technical Strengths, 
     Practical Implementation, Optimization Suggestions
   - Избегает дублирования базового анализа

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
[
  {
    "prompt_text": "Analyze this dataset...",
    "expert_description": "...",
    "why_good": "...",
    "scores": {...},
    "total_score": 26,
    "rank": 1,
    "example_output": "Based on the dataset analysis..." // НОВОЕ
    "expert_commentary": "**EFFECTIVENESS ANALYSIS:**..." // НОВОЕ
  }
]
```
**📁 Артефакты:**
- `enriched_prompts.json` - полные промпты с примерами и комментариями
- 🆕 `llm_requests/prompt_1_example_request.json` - запрос примера
- 🆕 `llm_requests/prompt_1_commentary_request.json` - запрос комментария 
- 🆕 `llm_responses_raw/prompt_1_example_response.txt` - сырой ответ примера
- 🆕 `llm_responses_raw/prompt_1_commentary_response.txt` - сырой ответ комментария

---

### Этап 10: Сборка финальной статьи (Article Assembly) 🤖

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Полностью обогащенные промпты из этапа 9
- Промпт-шаблон `prompts/prompt_collection/04_assemble_article.txt`  
- `topic` для персонализации статьи
- Все данные: prompt_text, expert_description, scores, examples, commentary

**🎯 ЦЕЛЬ:** Создать профессиональную публикационную статью 2000+ слов с полной структурой

**⚙️ ФУНКЦИИ:**
- `src/llm_processing.py` → `assemble_final_article()` - главная функция
- DeepSeek R1 Reasoner для структурирования и написания
- Профессиональное форматирование Markdown
- SEO-оптимизация заголовков и структуры

**🔄 ПРОЦЕСС:**
1. **Подготовка данных:** Все обогащенные промпты сериализуются в JSON
2. **LLM структурирование:** DeepSeek R1 создает:
   - Профессиональное введение с контекстом темы
   - Структурированные секции для каждого промпта
   - Практические примеры использования
   - Экспертные рекомендации по оптимизации
   - SEO-дружелюбные заголовки и подзаголовки
3. **Форматирование:** Финальная Markdown статья с:
   - Оглавление (TOC)
   - Правильная иерархия заголовков
   - Code blocks для промптов
   - Практические секции

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```markdown
# Best Prompts for Data Analysis in 2025: Expert Guide

## Table of Contents
- [Introduction](#introduction)
- [Top Data Analysis Prompts](#top-prompts)
  - [1. Advanced Dataset Analysis Prompt](#prompt-1)
  - [2. Statistical Insights Generator](#prompt-2)
...

## Introduction
Data analysis has become crucial...

## Top Data Analysis Prompts

### 1. Advanced Dataset Analysis Prompt

**Prompt:**
```
Analyze this dataset and provide insights on...
```

**Why This Works:**
This prompt is effective because...

**Example Output:**
Based on the dataset analysis...

**Expert Commentary:**
**EFFECTIVENESS ANALYSIS:** ...
```

**📁 Артефакты:**
- `final_article.md` - готовая статья для публикации (2000+ слов)
- 🆕 `llm_requests/assemble_article_request.json` - полный запрос с данными
- 🆕 `llm_responses_raw/assemble_article_response.txt` - сырая статья от LLM

---

## 🔧 **Техническая архитектура и управление**

### **Управление этапами:**
```bash
# Запуск конкретных этапов для отладки
python main.py "тема" --stage 7  # Остановка после извлечения промптов
python main.py "тема" --stage 8  # Остановка после ранжирования
python main.py "тема" --stage 9  # Остановка после обогащения
python main.py "тема"            # Полный пайплайн (этап 10)
```

### **Поток данных между этапами:**
```
Этап 7: cleaned_content → [{prompt_text, expert_description, why_good, how_to_improve}]
           ↓
Этап 8: all_prompts → {data: [{...промпты с scores, total_score, rank}]}
           ↓  
Этап 9: ranked_prompts → enriched_prompts с example_output и expert_commentary
           ↓
Этап 10: enriched_prompts → final_article.md
```

### **Обработка ошибок:**
- **Робастный JSON парсинг** с 4 стратегиями fallback
- **Полное логирование запросов/ответов** для отладки
- **Graceful degradation** при сбоях LLM вызовов
- **Валидация этапов** перед переходом к следующему

### **Оптимизация производительности:**
- **Конкурентный скрапинг** (настройка через CONCURRENT_REQUESTS)
- **Умное кэширование** через сохранение артефактов
- **Токен оптимизация** (200 для примеров, 600 для комментариев)
- **Прогрессивное улучшение** (каждый этап развивает предыдущий)

### **Ключевые принципы дизайна:**
1. **Детерминистичный вывод**: Каждый этап производит согласованные, воспроизводимые результаты
2. **Полная прозрачность**: Комплексное логирование всех LLM взаимодействий для отладки
3. **Сохранение контекста**: Потоки данных сохраняют всю релевантную информацию между этапами
4. **Фокус на качестве**: Множественные этапы фильтрации и скоринга обеспечивают высокое качество контента
5. **Модульность**: Каждый этап может быть запущен независимо для отладки и тестирования
6. **Chain of Thought**: DeepSeek R1 Reasoner обеспечивает продвинутые возможности рассуждения
7. **Прогрессивное улучшение**: Поздние этапы строятся на основе и улучшают ранний анализ

Эта архитектура обеспечивает надежную, высококачественную генерацию контента с полной видимостью процесса для отладки и оптимизации.
