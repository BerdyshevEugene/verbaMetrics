
[![Ruff](https://github.com/BerdyshevEugene/verbaMetrics/actions/workflows/ruff.yml/badge.svg?cache=buster)](https://github.com/BerdyshevEugene/verbaMetrics/actions/workflows/ruff.yml)

## verbaMetrics

<details>

a program for extracting the necessary keywords from the context. Uses lemmatization, takes data from the queue in RabbitMQ, performs processing and sends it to the queue. It works in conjunction with datagate and v2t

программа для выделения необходимых ключевых слов из контекста. Использует лемматизацию, берет данные из очереди в RabbitMQ, производит обработку и отправляет в очередь. Работает в связке с datagate и v2t.

</details>

---

## Структура проекта:

<details>

```python
verbaMetrics
│
├── src
│   ├── handlers - обработчики полученного текста
│   │   ├── dict.py - содержит словари (target_words), стоп-слова (stop_words)
│   │   ├── message_handler.py - обработка данных из RabbitMQ
│   │   └── text_processor.py - содержит класс TextProcessor для обработки данных 
│   │
│   ├── logger
│   ├── logs
│   │
│   └── rabbitmq
│       ├── connection.py - подключение и регистрация обработчика сообщений
│       └── publisher.py - отправка данных в rabbitmq
│
│
├── main.py
├── .env - прописывается служебная информация
├── requirements.txt - зависимости
└── README.md
```

</details>

---

## Установка и использование UV

<details>
<summary>📦 Способы установки UV</summary>

### 1. Установка через автономные установщики (рекомендуется)

**Для macOS и Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Для Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Установка через PyPI (альтернативный способ)
```bash
pip install uv
```

### Обновление UV
После установки вы можете обновить UV до последней версии:
```bash
uv self update
```

🔗 Подробнее об установке: [Официальная документация](https://docs.astral.sh/uv/getting-started/installation/)
</details>

---

<summary>🚀 Основные команды UV</summary>

<details>

### Управление Python-окружением

**Установка конкретной версии Python:**
```bash
uv python install 3.11  # Установит Python 3.11
```

### Управление зависимостями

**Синхронизация зависимостей проекта:**
```bash
uv sync  # Аналог pip install + pip-compile
```

**Запуск команд в окружении проекта:**
```bash
uv run <COMMAND>  # Например: uv run pytest
```

</details>

---

<summary>🔍 Интеграция с Ruff</summary>

<details>

[Ruff](https://github.com/astral-sh/ruff) - это молниеносный линтер для Python, также разработанный Astral.

**Установка Ruff через UV:**
```bash
uvx ruff  # Установит последнюю версию Ruff
```

**Проверка кода с помощью Ruff:**
```bash
uvx ruff check .  # Проверит все файлы в текущей директории
```
</details>

---

## Инструкция по запуску проекта

<details>

### Установка и запуск окружения:
```bash
uv venv -p 3.11 .venv  # создаём виртуальное окружение на python 3.11
uv pip install -r requirements.txt  # ставим зависимости
```

### Запуск программы:
```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 7999 --reload
```

</details>

---

## Запуск проекта в Docker

<details>

### Сборка
1. Авторизация в Docker Hub 
```
docker login
``` 
2. Сборка Docker-образа
```
docker build -t gsssupport/verbaMetrics_transcriberapp:latest .
```
3. Публикация образа в Docker Hub
```
docker push gsssupport/verbaMetrics_transcriberapp:latest
```

### Запуск
1. Авторизация в Docker Hub
```
docker login
``` 
2. Запуск Docker-контейнера
```
docker-compose up
```

</details>

---

## Остальная информация

<details>

```
CompanyName: GMG
FileDescription: verbaMetrics
InternalName: verbaMetrics
ProductName: verbaMetrics
Author: Berdyshev E.A.
Development and support: Berdyshev E.A.
LegalCopyright: © GMG. All rights reserved.
```

</details>
