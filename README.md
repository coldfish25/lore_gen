# LoreBot - Astrology Knowledge Automation

Универсальный микросервис для генерации астрологических знаний с помощью LLM (ChatGPT) и сохранения их в структурированном JSON формате.

## Использование

### Основной запуск
```bash
python main.py
```

### Универсальный генератор
```bash
python generator.py <template_path> <base_filename> <data_path>
```

**Пример для зодиаков:**
```bash
python generator.py config/zodiac_prompt.txt zodiacs config/zodiac.json
```

### Использование в коде
```python
from generator import UniversalGenerator
from config.settings import Settings

settings = Settings()
generator = UniversalGenerator(settings)

results = await generator.generate_data(
    template_path="config/zodiac_prompt.txt",
    base_filename="zodiacs.json", 
    data_path="config/zodiac.json"
)
```

## Как это работает

1. **Шаблон промпта** (`config/zodiac_prompt.txt`) - содержит плейсхолдеры `{key}`, `{element}`, etc.
2. **Данные** (`config/zodiac.json`) - массив объектов с полями для подстановки
3. **Языки** (`config/languages.json`) - поддерживаемые языки генерации
4. **Генератор** заполняет шаблон данными и отправляет в LLM
5. **Результат** сохраняется как `{language}_{filename}.json` в папке `data/`

## Добавление новых категорий

1. Создайте шаблон промпта: `config/new_category_prompt.txt`
2. Создайте данные: `config/new_category.json`
3. Запустите генератор:
```bash
python generator.py config/new_category_prompt.txt new_category config/new_category.json
```

## Структура выходных файлов

```json
{
  "generated_at": "2025-08-25T10:30:00",
  "language": "eng",
  "total_items": 12,
  "data": [
    {
      "key": "aries",
      "content": "Generated LLM response..."
    }
  ]
}
```

## Структура проекта

```
LoreBot/
├── main.py                    # Основной запуск
├── generator.py               # Универсальный генератор
├── config/                    # Конфигурация
│   ├── settings.py           # Настройки приложения
│   ├── languages.json        # Поддерживаемые языки
│   ├── zodiac.json          # Данные знаков зодиака
│   └── zodiac_prompt.txt    # Шаблон промпта для зодиаков
├── examples/                 # Примеры использования
├── utils/                    # Утилиты
├── data/                     # Выходные JSON файлы
└── requirements.txt          # Зависимости
```
