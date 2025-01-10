# verbaMetrics

a program for extracting the necessary keywords from the context. Uses lemmatization, takes data from the queue in RabbitMQ, performs processing and sends it to the queue. It works in conjunction with datagate and v2t
---
программа для выделения необходимых ключевых слов из контекста. Использует лемматизацию, берет данные из очереди в RabbitMQ,  производит обработку и отправляет в очередь. Работает в связке с datagate и v2t.


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
│   ├── log
│   │
│   └── rabbitmq
│       └── connection.py - подключение и регистрация обработчика сообщений
│
├── main.py
├── .env - прописывается служебная информация
├── requirements.txt - зависимости
└── README.md
```

## Инструкция
1. создайте и активируйте виртуальное окружение и установите зависимости:
```python
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. в папке socket_handler создайте файл `.env`. В нем `пропишите значения для глобальных переменных`:
- MW_DB_HOST
- MW_DB_PORT
- HOST = localhost
- PORT = localport
- MW_DB_USER
- MW_DB_PASS
- MW_DB_NAME

3. запустите сокет:
```python
cd src/
uvicorn main:app --host 0.0.0.0 --port 7999
```

## Остальная информация
CompanyName: GMG

FileDescription: verbaMetrics

InternalName: verbaMetrics

LegalCopyright: © GMG. All rights reserved.

OriginalFilename: -

ProductName: verbaMetrics

Author: Berdyshev E.A.

Development and support: Berdyshev E.A.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

