# 🤖 SmartHouse AI — Telegram Бот для управления умным домом

SmartHouse AI — это Telegram-бот на базе Python и Aiogram, предназначенный для управления устройствами умного дома с помощью текстовых и голосовых команд. Бот поддерживает авторизацию, добавление и управление девайсами, а также интеграцию с Retrieval-Augmented Generation (RAG) для обработки запросов пользователей.

## 🚀 Возможности

- Управление собственными умными устройствами (лампочки, розетки и т. д.)
- Регистрация и авторизация пользователей
- Добавление и просмотр подключённых девайсов
- Обработка голосовых и текстовых команд
- Интеграция RAG для более «умного» взаимодействия
- Удобное главное меню и подразделы

## 🧠 Используемые технологии

- Python 3.10+
- Aiogram
- PostgreSQL
- SQLAlchemy
- Pydantic
- Langchain Groq
- Docker / Docker Compose

## 📁 Структура проекта
```
SmartHouse-AI/
├── bot/
|   ├── AI/
|   │   └── llm.py                  # обработка команд через LLM c RAG
|   ├── db/
|   │   ├── base.py                 # Базовая настройка БД
|   │   └── service.py              # Утилиты взаимодействия с БД
|   ├── devices/
|   │   ├── handler.py              # Хэндлеры управления устройствами
|   │   ├── keyboards.py            # Клавиатуры/меню для девайсов
|   │   ├── model.py                # Модели устройств
|   │   ├── service.py              # Сервисная логика устройств
|   │   └── states.py               # Состояния FSM для работы с девайсами
|   ├── general/
|   │   ├── handler.py              # Общие хэндлеры
|   │   ├── keyboards.py            # Общие клавиатуры
|   │   └── voice.py                # Обработка голосовых сообщений
|   ├── migrations/                 # Миграции Alembic
|   ├── users/
|   │   ├── handler.py              # Хэндлеры пользователей
|   │   ├── keyboards.py            # Клавиатуры для работы с пользователями
|   │   ├── model.py                # Модели пользователей
|   │   ├── service.py              # Сервисная логика пользователей
|   │   └── states.py               # Состояния FSM для регистрации/авторизации
|   ├── config.py                   # Конфигурация приложения
|   ├── main.py                     # Точка входа
|   └── middleware.py               # Middleware для Aiogram
├── .env.example
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## ⚙️ Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/Mifrain/SmartHouse-AI.git
cd SmartHouse-AI
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе предоставленного шаблона `.env.example` и заполните необходимые переменные:

```bash
cp .env.example .env
```

### 3. Запуск с помощью Docker

Убедитесь, что у вас установлен Docker и Docker Compose. Затем выполните:

```bash
docker-compose up --build
```

Это создаст и запустит контейнеры, необходимые для работы

## 📌 Примеры взаимодействия

- 🔐 Авторизация: ввод токена/сессии
- ➕ Добавить устройство: выбор из списка + ввод имени
- 💡 Управление: «включи свет», «проверь камеру»
- 🎤 Голосовые команды: обрабатываются RAG-интеграцией
