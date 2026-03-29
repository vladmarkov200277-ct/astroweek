"""
FastAPI-сервер: принимает запросы от Mini App, возвращает прогноз.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import re

from astro import build_astro_report
from forecast import generate_forecast

logger = logging.getLogger(__name__)

app = FastAPI(title="AstroWeek API", version="1.0.0")

# CORS — разрешаем запросы от Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Отдаём фронтенд ─────────────────────────────────────────────────────────
import os
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")


# ─── Схемы запроса / ответа ──────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    birth_date: str   # "DD.MM.YYYY"
    birth_time: str   # "HH:MM"
    city: str

    @field_validator("birth_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", v):
            raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ")
        day, month, year = v.split(".")
        if not (1 <= int(day) <= 31 and 1 <= int(month) <= 12 and 1900 <= int(year) <= 2010):
            raise ValueError("Некорректная дата рождения")
        return v

    @field_validator("birth_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Время должно быть в формате ЧЧ:ММ")
        h, m = v.split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("Некорректное время")
        return v

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Введите название города")
        return v


# ─── Роуты ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/forecast")
async def get_forecast(req: ForecastRequest):
    """Основной эндпоинт: принимает данные рождения, возвращает прогноз."""
    logger.info(f"Forecast request: {req.birth_date} {req.birth_time} {req.city}")

    try:
        # 1. Рассчитываем астрологические данные
        report = build_astro_report(
            birth_date=req.birth_date,
            birth_time=req.birth_time,
            city=req.city,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Astro calculation error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при расчёте натальной карты")

    try:
        # 2. Генерируем прогноз через Claude
        forecast = await generate_forecast(report)
    except Exception as e:
        logger.error(f"Forecast generation error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при генерации прогноза")

    # 3. Формируем ответ
    natal = report.natal
    return {
        "natal": {
            "sun": {
                "sign": natal.sun.sign_ru,
                "symbol": natal.sun.sign_symbol,
                "degree": natal.sun.degree,
            },
            "moon": {
                "sign": natal.moon.sign_ru,
                "symbol": natal.moon.sign_symbol,
                "degree": natal.moon.degree,
            },
            "ascendant": {
                "sign": natal.ascendant_ru,
                "symbol": natal.ascendant_symbol,
            },
            "planets": [
                {
                    "name": p.name_ru,
                    "sign": p.sign_ru,
                    "symbol": p.sign_symbol,
                    "retrograde": p.retrograde,
                }
                for p in natal.planets
            ],
        },
        "transits": [
            {
                "name": t.name_ru,
                "sign": t.sign_ru,
                "retrograde": t.retrograde,
            }
            for t in report.transits
        ],
        "forecast": forecast,
        "week_start": report.week_start,
        "week_end": report.week_end,
    }
