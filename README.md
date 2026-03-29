# AstroWeek · @BLONDY_club

Telegram Mini App — персональный астрологический прогноз на неделю.

## Структура проекта

```
astroweek/
├── backend/
│   ├── main.py          # Точка входа (бот + сервер)
│   ├── bot.py           # Telegram-бот (aiogram 3)
│   ├── server.py        # FastAPI REST API
│   ├── astro.py         # Расчёт натальной карты (kerykeion)
│   ├── forecast.py      # Генерация прогноза (Claude API)
│   ├── config.py        # Конфигурация из .env
│   └── requirements.txt
├── frontend/
│   └── index.html       # Telegram Mini App (vanilla JS)
├── .env.example
└── README.md
```

## Быстрый старт

### 1. Получите токены

- **Telegram Bot Token** — создайте бота у [@BotFather](https://t.me/BotFather)
- **Claude API Key** — [console.anthropic.com](https://console.anthropic.com)
- **Хостинг с HTTPS** — Telegram Mini App требует HTTPS (Railway, Render, VPS + nginx)

### 2. Установите зависимости

```bash
cd backend
pip install -r requirements.txt
```

### 3. Настройте окружение

```bash
cp .env.example .env
# Отредактируйте .env — укажите BOT_TOKEN, WEBAPP_URL, ANTHROPIC_API_KEY
```

### 4. Разместите фронтенд

Папку `frontend/` нужно отдавать по HTTPS. Проще всего:

**Вариант A — FastAPI отдаёт сам** (уже настроено):
Фронтенд будет доступен по `https://your-domain.com/app`
Укажите `WEBAPP_URL=https://your-domain.com` в `.env`

**Вариант B — Nginx + статика:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    location /app {
        root /var/www/astroweek/frontend;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 5. Запустите

```bash
cd backend
python main.py
```

Бот и API сервер запустятся одновременно.

### 6. Зарегистрируйте Mini App у BotFather

```
/newapp → выберите вашего бота → укажите URL: https://your-domain.com/app
```

## API

### `POST /api/forecast`

**Тело запроса:**
```json
{
  "birth_date": "15.03.1995",
  "birth_time": "14:30",
  "city": "Москва"
}
```

**Ответ:**
```json
{
  "natal": {
    "sun": { "sign": "Рыбы", "symbol": "♓", "degree": 24.5 },
    "moon": { "sign": "Скорпион", "symbol": "♏", "degree": 12.3 },
    "ascendant": { "sign": "Лев", "symbol": "♌" },
    "planets": [...]
  },
  "transits": [...],
  "forecast": {
    "summary": "Неделя благоприятна для...",
    "favorable_days": ["Вторник", "Среда"],
    "caution_days": ["Четверг"],
    "career": { "rating": 4, "text": "..." },
    "relationships": { "rating": 3, "text": "..." },
    "health": { "rating": 2, "text": "..." }
  },
  "week_start": "30.03.2026",
  "week_end": "05.04.2026"
}
```

## Деплой на Railway (рекомендуется)

1. Создайте аккаунт на [railway.app](https://railway.app)
2. Создайте новый проект → Deploy from GitHub
3. Укажите `Root Directory: backend`
4. Добавьте переменные окружения из `.env`
5. Railway автоматически выдаст HTTPS домен — укажите его как `WEBAPP_URL`

## Стек

| Компонент | Технология |
|-----------|-----------|
| Бот | Python + aiogram 3.7 |
| API | FastAPI + uvicorn |
| Астрология | kerykeion (Swiss Ephemeris) |
| Геокодинг | geopy + timezonefinder |
| AI прогноз | Claude claude-opus-4-6 |
| Фронтенд | Vanilla JS + CSS |
