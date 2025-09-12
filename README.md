# 🤖 AI Content Generator

Автоматизированный пайплайн для генерации высококачественного контента о промптах с публикацией в WordPress.

## ✨ Основные возможности

- **8-этапный пайплайн**: Поиск источников → Обработка → Генерация → WordPress публикация (автоматически)
- **Multi-LLM система**: Google Gemini 2.5 Flash Lite + DeepSeek Reasoner (редактирование по умолчанию)  
- **WordPress интеграция**: Автоматическая публикация на https://ailynx.ru с Yoast SEO
- **Token tracking**: Детальная аналитика использования
- **Русский язык**: Специализация на российскую аудиторию

---

## 🏃‍♂️ Быстрый старт

### 1. Установка
```bash
pip install -r requirements.txt
```

### 2. API ключи в .env файле
```bash
FIRECRAWL_API_KEY=your_key
OPENROUTER_API_KEY=your_key  # Основной (для Gemini 2.5)
DEEPSEEK_API_KEY=your_key    # Опционально (для альтернативных моделей)
```

### 3. Запуск
```bash
# Генерация статьи с автоматической публикацией в WordPress (по умолчанию)
python3 main.py "Ваша тема"

# Генерация без публикации в WordPress  
python3 main.py "Ваша тема" --no-publish

# Использование другой модели для редакторской проверки (по умолчанию deepseek-reasoner)
python3 main.py "Ваша тема" --editorial-model "google/gemini-2.5-flash-lite-preview-06-17"

# Полный контроль над всеми 3 этапами пайплайна
python3 main.py "Ваша тема" --extract-model deepseek-chat --generate-model openai/gpt-4o --editorial-model deepseek-reasoner
```

---

## 📋 Как это работает

1. **Поиск** - Находит 20 релевантных URL по теме
2. **Парсинг** - Извлекает контент с найденных сайтов  
3. **Оценка** - Ранжирует источники по качеству
4. **Отбор** - Выбирает топ-5 лучших источников
5. **Очистка** - Убирает "мусор" из контента
6. **Извлечение** - LLM извлекает промпты из источников (2 промпта на источник, 10 всего)
7. **Генерация** - LLM создает готовую статью на русском
8. **Публикация** - Автоматически публикует в WordPress (опционально)

### 🔍 Мониторинг процесса

Pipeline включает детальный мониторинг извлечения промптов:
- **Ожидаемо**: 10 промптов из 5 источников (по 2 с каждого)
- **Автоматическое исправление**: JSON parsing ошибок от LLM
- **Отчетность**: Статистика успешности извлечения в реальном времени
- **Предупреждения**: Уведомления о проблемных источниках

## 🧪 Тестирование WordPress

```bash
# Создание категории (одноразово)
python3 create_prompts_category.py

# Тест публикации
python3 test_publication_auto.py
```

## 📊 Результат работы

Все артефакты сохраняются в `output/Your_Topic/`:
- Найденные промпты (`all_prompts.json`)
- Готовая статья (`wordpress_data.json`) 
- Отчет по токенам (`token_usage_report.json`)
- Результат публикации (`wordpress_publication_result.json`)

**WordPress публикация:**
- Сайт: https://ailynx.ru
- Категория: "prompts" (ID: 825)
- Статус: draft (для проверки)
- Yoast SEO: Custom Post Meta Endpoint для записи мета-полей
- Автоматическое заполнение всех SEO полей

## 📋 Changelog

### 🎉 September 11, 2025 - Google Gemini 2.5 Integration

**Основные изменения:**
- **✅ Решена проблема с обрезанием статей**: Переход на Google Gemini 2.5 Flash Lite (65K токенов vs 8K)
- **🚀 Новая модель по умолчанию**: `google/gemini-2.5-flash-lite-preview-06-17` для всех этапов
- **📈 Улучшенное качество**: Gemini использует ВСЕ переданные промпты (в отличие от GPT-4o)
- **⚡ Система флагов**: Полный контроль через `--extract-model`, `--generate-model` и `--editorial-model`

**Обновления API:**
- **OPENROUTER_API_KEY** теперь ОБЯЗАТЕЛЬНЫЙ (для Gemini 2.5)
- **DEEPSEEK_API_KEY** опционален (для альтернативных моделей)

**Доступные модели:**
- `google/gemini-2.5-flash-lite-preview-06-17` (65K) - **По умолчанию**
- `google/gemini-2.0-flash-001` (8K) - Базовая Gemini
- `deepseek-reasoner`, `openai/gpt-4o`, `openai/gpt-4o-mini` - Альтернативы

## 📚 Документация

- **[docs/flow.md](docs/flow.md)** - Детальное описание каждого этапа
- **[docs/WORDPRESS_INTEGRATION.md](docs/WORDPRESS_INTEGRATION.md)** - WordPress интеграция
- **[docs/FEATURE_OVERVIEW.md](docs/FEATURE_OVERVIEW.md)** - Полный обзор возможностей

---

**Время выполнения**: ~6-10 минут | **Токенов**: ~35k | **Статус**: ✅ Готов к использованию