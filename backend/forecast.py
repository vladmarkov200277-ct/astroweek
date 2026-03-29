"""
Генерация астрологического прогноза через Claude API.
"""

import json
from anthropic import AsyncAnthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from astro import AstroReport


client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


def _build_astro_context(report: AstroReport) -> str:
    """Формирует структурированный контекст из астрологических данных."""

    natal = report.natal

    # Натальные планеты
    planets_str = "\n".join(
        f"  • {p.name_ru} в {p.sign_ru}{' (ретро)' if p.retrograde else ''} ({p.degree}°)"
        for p in natal.planets
    )

    # Текущие транзиты
    transits_str = "\n".join(
        f"  • {p.name_ru} сейчас в {p.sign_ru}{' (ретро)' if p.retrograde else ''} ({p.degree}°)"
        for p in report.transits
    )

    # Значимые транзитные аспекты (только гармоничные и напряжённые)
    key_aspects = [a for a in report.transit_aspects if a.aspect in
                   ("conjunction", "opposition", "trine", "square", "sextile")][:12]
    aspects_str = "\n".join(
        f"  • {a.planet1} — {a.aspect_ru} ({a.nature}) — {a.planet2} (орбис {a.orbit}°)"
        for a in key_aspects
    )

    # Натальные аспекты (топ-8)
    natal_asp_str = "\n".join(
        f"  • {a.planet1} — {a.aspect_ru} — {a.planet2}"
        for a in report.natal_aspects[:8]
    )

    return f"""
НАТАЛЬНАЯ КАРТА ПОЛЬЗОВАТЕЛЯ:
Солнце: {natal.sun.sign_ru} ({natal.sun.degree}°)
Луна: {natal.moon.sign_ru} ({natal.moon.degree}°)
Асцендент: {natal.ascendant_ru}

Планеты в натальной карте:
{planets_str}

Ключевые натальные аспекты:
{natal_asp_str}

ТЕКУЩЕЕ ПОЛОЖЕНИЕ ПЛАНЕТ (транзиты):
{transits_str}

ТРАНЗИТНЫЕ АСПЕКТЫ К НАТАЛЬНОЙ КАРТЕ:
{aspects_str}

ПЕРИОД ПРОГНОЗА: {report.week_start} — {report.week_end}
""".strip()


SYSTEM_PROMPT = """Ты — опытный астролог, создающий персональные еженедельные прогнозы.
Ты работаешь от имени канала @BLONDY_club — это женский лайфстайл-проект, стиль общения: тёплый, поддерживающий, немного поэтичный, но без излишней мистики. Говоришь «вы».

Твоя задача — составить прогноз на неделю на основе натальной карты и текущих планетарных транзитов.

ПРАВИЛА:
1. Всегда опирайся на конкретные аспекты и транзиты из данных, не выдумывай
2. Раздели прогноз на 3 сферы: Карьера и финансы, Отношения и близкие, Здоровье и энергия
3. Для каждой сферы укажи рейтинг от 1 до 5
4. Укажи 2–3 благоприятных дня недели и 1–2 дня, когда лучше быть осторожнее
5. Добавь краткий общий совет на неделю (1–2 предложения)
6. Стиль: живой, тёплый, конкретный — без шаблонных фраз типа «звёзды благоволят»
7. Ответ строго в формате JSON (без markdown-обёртки)
"""

FORECAST_SCHEMA = {
    "summary": "Общий совет на неделю (1-2 предложения)",
    "favorable_days": ["Вторник", "Среда"],
    "caution_days": ["Четверг"],
    "career": {
        "rating": 4,
        "text": "Текст прогноза по карьере (2-3 предложения)"
    },
    "relationships": {
        "rating": 3,
        "text": "Текст прогноза по отношениям (2-3 предложения)"
    },
    "health": {
        "rating": 2,
        "text": "Текст прогноза по здоровью (2-3 предложения)"
    }
}


async def generate_forecast(report: AstroReport) -> dict:
    """Генерирует прогноз через Claude и возвращает структурированный словарь."""

    astro_context = _build_astro_context(report)

    user_message = f"""Вот астрологические данные пользователя:

{astro_context}

Составь недельный прогноз строго в формате JSON по этой схеме:
{json.dumps(FORECAST_SCHEMA, ensure_ascii=False, indent=2)}

Верни только валидный JSON, без каких-либо пояснений до или после."""

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Убираем возможные markdown-блоки если модель всё же их добавила
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)
