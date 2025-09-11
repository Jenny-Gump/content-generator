# Pipeline Flow Description (Updated)

This document provides a detailed, step-by-step breakdown of the simplified content generation pipeline for WordPress article generation.

**MAJOR UPDATE**: The pipeline has been significantly simplified to focus on WordPress article generation for prompt collections. We now have a streamlined 7-stage process that ends with a complete WordPress-ready article.

## 🎛️ Multi-Provider LLM System (September 2025)

Major architectural upgrade for flexible model selection and provider support:

### **Multi-Provider Architecture**
- **DeepSeek Provider**: Primary provider with reasoning capabilities (`deepseek-reasoner`, `deepseek-chat`)
- **OpenRouter Provider**: Gateway to OpenAI models (`openai/gpt-4o`, `openai/gpt-4o-mini`, etc.)
- **Dynamic Client Selection**: Automatic provider detection based on model name
- **Cached Client Management**: Performance-optimized client reuse

### **Command Line Model Override**
- **`--extract-model`**: Override model for prompt extraction stage
- **`--generate-model`**: Override model for article generation stage
- **Real-time Logging**: Model overrides are logged during pipeline execution

### **Enhanced Token Tracking**
- **Provider Metadata**: Track which provider/model was used for each request
- **Multi-Provider Reports**: Token usage breakdown by provider in session summaries
- **Model-Specific Analytics**: Detailed usage statistics per model type

**Benefits**:
- 🎯 **Task-Optimized Models**: Use fast models for extraction, powerful models for generation
- 💰 **Cost Control**: Mix free DeepSeek models with paid OpenAI models strategically
- ⚡ **Performance Tuning**: Choose optimal speed/quality tradeoff for each stage
- 📊 **Comprehensive Tracking**: Full visibility into multi-provider token usage

## 🔧 Content Cleaning Optimization (September 2025)

Major improvements to content cleaning pipeline for better quality and efficiency:
- **Enhanced Firecrawl Filtering**: Added `excludeTags` and `includeTags` for precise HTML element filtering
- **Improved Regex Patterns**: Fixed image removal bugs, expanded UI element detection
- **Structural Cleaning**: Duplicate block removal, minimum line length filtering
- **Quality Metrics**: Real-time tracking of cleaning efficiency (before/after statistics)

**Benefits**:
- ⬇️ **50-70% content reduction** while preserving valuable information
- 🎯 **Higher extraction quality** with less noise in LLM inputs
- ⚡ **Faster processing** due to reduced content volume
- 📊 **Transparent monitoring** with detailed cleaning metrics

## 🔍 LLM Debugging Features (January 2025)

All LLM interactions are automatically logged for debugging:
- **Full Request Logging**: Every prompt sent to LLM providers (DeepSeek/OpenRouter)
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

### Этап 3: Оценка (Scoring)

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

### Этап 4: Отбор (Selection)

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

### Этап 5: Очистка (Cleaning)

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
**📁 Артефакт:**
- `final_cleaned_sources.json` - JSON со всеми очищенными источниками

---

### Этап 6: Извлечение промптов (Prompt Extraction) 🤖

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

### Этап 7: Генерация WordPress статьи (WordPress Article Generation) 🤖

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Все извлеченные промпты из этапа 6 (обычно 15-30 промптов)
- Промпт-шаблон `prompts/prompt_collection/01_generate_wordpress_article.txt`
- `topic` из командной строки для персонализации
- Gemini 2.5 Flash Lite API credentials

**🎯 ЦЕЛЬ:** Создать черновую WordPress статью на русском языке с улучшенными промптами и экспертными комментариями

**⚙️ ФУНКЦИИ:**
- `src/llm_processing.py` → `generate_wordpress_article()` - главная функция
- Gemini 2.5 Flash Lite для создания высококачественного контента
- HTML форматирование совместимое с WordPress
- SEO-оптимизация для российской аудитории

**🔄 ПРОЦЕСС:**
1. **Подготовка данных:** Все промпты из `all_prompts.json` передаются в LLM
2. **LLM генерация:** Gemini 2.5 Flash Lite создает:
   - Профессиональное введение на тему промптов для {topic}
   - Секцию с основами создания промптов (Role, Context, Main goal, Style, Constraints + CoT)
   - Коллекцию улучшенных промптов с экспертными описаниями
   - Практические примеры и случаи использования
   - Продвинутые техники и рекомендации
   - SEO-оптимизированные заголовки на русском языке
3. **Форматирование:** WordPress-готовая HTML разметка с:
   - Правильная структура заголовков `<h2>`, `<h3>`
   - Код блоки `<pre><code>` для промптов
   - Списки `<ul>`, `<li>` для читаемости
   - `<strong>` и `<blockquote>` для выделения

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "title": "Лучшие промпты для анализа данных: Полное руководство 2025",
  "content": "<h2>Введение</h2><p>Качественные промпты для анализа данных могут кардинально изменить...</p><h2>Основы создания промптов</h2><p>Эффективный промпт состоит из ключевых элементов:</p><ul><li><strong>Role (Роль)</strong> - определение роли для ИИ</li><li><strong>Context (Контекст)</strong> - предоставление фона</li></ul>...",
  "excerpt": "Подробное руководство по созданию эффективных промптов для анализа данных с экспертными рекомендациями и практическими примерами",
  "slug": "luchshie-prompty-dlya-analiza-dannykh-rukovodstvo-2025",
  "categories": ["prompts"],
  "_yoast_wpseo_title": "Лучшие промпты для анализа данных 2025",
  "_yoast_wpseo_metadesc": "Экспертные промпты для анализа данных с практическими примерами и рекомендациями. Полное руководство 2025",
  "image_caption": "Источник: www.example.com",
  "focus_keyword": "промпты для анализа данных"
}
```

**📁 Артефакты:**
- `wordpress_data.json` - черновая структура для WordPress с метаданными (содержит блочные теги)
- `article_content.html` - HTML контент статьи для удобства
- 🆕 `llm_requests/generate_wordpress_article_request.json` - полный запрос
- 🆕 `llm_responses_raw/generate_wordpress_article_response.txt` - сырой JSON ответ от LLM

**💡 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:**
- **Структурированный JSON:** Готовая структура для обработки редактором
- **Русский язык:** Вся статья на русском для https://ailynx.ru  
- **WordPress блочные теги:** Содержит `<!-- wp:paragraph -->` и подобные теги (будут удалены на этапе 8)
- **SEO метаданные:** title, excerpt, slug, Yoast SEO поля
- **Улучшение промптов:** LLM дорабатывает исходные промпты до идеала
- **Автоматическая категоризация:** categories: ["prompts"]
- **Практический фокус:** Реальные случаи использования и примеры

---

### Этап 8: Редакторская обработка (Editorial Review) ✏️

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Черновая структура `wordpress_data.json` из этапа 7 (с блочными тегами)
- Промпт-шаблон `prompts/prompt_collection/02_editorial_review.txt`
- Gemini 2.5 Flash Lite API credentials

**🎯 ЦЕЛЬ:** Профессиональная редактура и очистка статьи для финальной публикации

**⚙️ ФУНКЦИИ:**
- `src/llm_processing.py` → `editorial_review()` - главная функция редакторской обработки
- Gemini 2.5 Flash Lite с низкой температурой (0.2) для стабильного редактирования
- Робастный JSON парсинг с обработкой ошибок

**🔄 ПРОЦЕСС:**
1. **Загрузка промпта:** Используется специальный промпт для редактора WordPress статей
2. **LLM редактура:** Gemini 2.5 Flash Lite выполняет:
   - Полную очистку от WordPress блочных тегов (`<!-- wp:paragraph -->`, `<!-- /wp:code -->` и т.д.)
   - Переформатирование промптов в читаемый вид внутри `<pre><code>` тегов
   - Улучшение структуры контента (таблицы, списки, абзацы)
   - Редакторский контроль текста (удаление "воды" и общих фраз)
   - Улучшение заголовков и метаданных (title, description, excerpt)
   - Исправление H2/H3 заголовков (только первая буква заглавная)
3. **Сохранение промптов:** Все промпты и технические детали остаются неизменными
4. **JSON валидация:** Многослойная проверка и парсинг результата

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "title": "Улучшенный заголовок без блочных тегов",
  "content": "<h2>Чистый HTML без WordPress блочных тегов</h2><p>Отформатированный контент с правильной структурой...</p>",
  "excerpt": "Привлекательное описание статьи",
  "slug": "optimized-url-slug", 
  "categories": ["prompts"],
  "_yoast_wpseo_title": "SEO-оптимизированный заголовок",
  "_yoast_wpseo_metadesc": "Интригующее мета-описание",
  "image_caption": "Источник: www.example.com",
  "focus_keyword": "ключевое слово"
}
```

**📁 Артефакты:**
- `wordpress_data_final.json` - финальная отредактированная статья без блочных тегов
- `article_content_final.html` - чистый HTML контент для просмотра
- `llm_requests/editorial_review_request.json` - запрос к редактору
- `llm_responses_raw/editorial_review_response.txt` - сырой ответ редактора

**💡 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:**
- **Полная очистка блочных тегов:** Удаление всех `<!-- wp:* -->` конструкций
- **Улучшенная читаемость:** Промпты разбиты на удобные строки
- **Профессиональное редактирование:** Убрана "вода", улучшен стиль
- **Сохранение содержания:** Все промпты и технические детали остаются
- **SEO-оптимизация:** Улучшенные заголовки и описания для людей
- **Fallback защита:** При ошибках возвращается оригинальный контент
- **Низкая температура:** Стабильное редактирование без творческих отклонений

---

### Этап 9: WordPress Publication (WordPress Publication) 🌐

**📥 ВХОДНЫЕ ДАННЫЕ:**
- Финальная отредактированная структура `wordpress_data_final.json` из этапа 8
- WordPress креденции из `.env` файла (PetrovA, app password)
- Флаг `--publish-wp` из командной строки
- WordPress API настройки

**🎯 ЦЕЛЬ:** Автоматически опубликовать статью на https://ailynx.ru в категории "prompts" в статусе черновика с полной поддержкой Yoast SEO

**⚙️ ФУНКЦИИ:**
- `src/wordpress_publisher.py` → `WordPressPublisher()` - главный класс
- `publish_article()` - основная функция публикации
- `test_wordpress_connection()` - тестирование соединения
- WordPress REST API v2 интеграция
- Автоматическое управление категориями

**🔄 ПРОЦЕСС:**
1. **Тестирование соединения:** Проверка WordPress API и аутентификации
2. **Подготовка данных:** Адаптация JSON структуры для WordPress REST API
3. **Обработка категорий:** Поиск или создание категории "prompts" (ID: 825)
4. **Публикация статьи:** POST запрос к `/wp-json/wp/v2/posts` с полными данными
5. **SEO метаданные:** Автоматическая установка Yoast SEO полей через meta
6. **Сохранение результата:** Логирование WordPress ID и URL для редактирования

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "success": true,
  "wordpress_id": 4377,
  "url": "https://ailynx.ru/wp-admin/post.php?post=4377&action=edit",
  "error": null
}
```

**📁 Артефакты:**
- `wordpress_publication_result.json` - результат публикации с WordPress ID
- Логи процесса публикации в основном лог-файле

**💡 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:**
- **Опциональность:** Активируется только с флагом `--publish-wp`
- **Безопасность:** Статьи создаются в статусе `draft` для проверки
- **SEO интеграция:** Автоматическое заполнение всех Yoast SEO полей
- **Категоризация:** Все статьи автоматически попадают в категорию "prompts"
- **Валидация:** Полная проверка соединения и креденций перед публикацией
- **Обработка ошибок:** Детальное логирование и graceful fallback при сбоях
- **Аккаунт PetrovA:** Специальный аккаунт для Content Generator публикаций

---

## 🔧 **Техническая архитектура и управление (ОБНОВЛЕНО)**

### **Запуск пайплайна:**
```bash
# Полный пайплайн с генерацией и редактурой (этапы 1-8)
python main.py "Лучшие промпты для создания идей для видео"

# Полный пайплайн с публикацией (этапы 1-9)
python main.py "Промпты для анализа данных" --publish-wp

# Кастомные модели с публикацией
python main.py "ChatGPT промпты для маркетинга" --generate-model openai/gpt-4o --publish-wp

# Создание категории WordPress (одноразово)
python create_prompts_category.py
```

### **Упрощенный поток данных:**
```
Этапы 1-6: Поиск, очистка и извлечение промптов
           ↓
Этап 7: all_prompts + topic → wordpress_data.json (черновая статья с блочными тегами)
           ↓
Этап 8: wordpress_data.json → editorial_review() → wordpress_data_final.json (чистая статья)
           ↓
Этап 9: wordpress_data_final.json → WordPress API → draft post (опционально)
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

### **Ключевые принципы дизайна (ОБНОВЛЕНО):**
1. **Простота и эффективность**: Полный 9-этапный пайплайн с обязательной редактурой
2. **WordPress-ориентированность**: Прямая генерация и автоматическая публикация контента
3. **Качественное улучшение промптов**: LLM дорабатывает найденные промпты до идеального состояния
4. **Профессиональная редактура**: Этап 8 обеспечивает качество публикации редактором-ИИ
5. **Полная прозрачность**: Комплексное логирование всех LLM и WordPress взаимодействий
6. **Русскоязычный фокус**: Специализация на российскую аудиторию и сайт ailynx.ru
7. **Gemini-powered**: Gemini 2.5 Flash Lite обеспечивает высококачественную генерацию и редактуру
8. **SEO-оптимизация**: Автоматическое заполнение Yoast SEO полей для поисковых систем
9. **Безопасная публикация**: Статьи создаются в статусе draft для проверки перед публикацией
10. **Практическая ценность**: Фокус на реальных случаях использования и экспертных рекомендациях

Эта полная 9-этапная архитектура обеспечивает быструю генерацию, профессиональную редактуру и автоматическую публикацию высококачественных WordPress статей о коллекциях промптов с полной готовностью к использованию.
