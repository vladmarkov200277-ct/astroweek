"""
Модуль астрологических расчётов.
Использует kerykeion (Swiss Ephemeris) для построения натальной карты
и расчёта текущих транзитов планет.
"""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from kerykeion import AstrologicalSubject, Report
from kerykeion.aspects import NatalAspects, SynastryAspects

from config import GEOPY_USER_AGENT


# ─── Символы и названия ──────────────────────────────────────────────────────

SIGN_NAMES_RU = {
    "Ari": "Овен",  "Tau": "Телец", "Gem": "Близнецы",
    "Can": "Рак",   "Leo": "Лев",   "Vir": "Дева",
    "Lib": "Весы",  "Sco": "Скорпион", "Sag": "Стрелец",
    "Cap": "Козерог","Aqu": "Водолей", "Pis": "Рыбы",
}

SIGN_SYMBOLS = {
    "Ari": "♈", "Tau": "♉", "Gem": "♊", "Can": "♋",
    "Leo": "♌", "Vir": "♍", "Lib": "♎", "Sco": "♏",
    "Sag": "♐", "Cap": "♑", "Aqu": "♒", "Pis": "♓",
}

PLANET_NAMES_RU = {
    "Sun":     "Солнце",
    "Moon":    "Луна",
    "Mercury": "Меркурий",
    "Venus":   "Венера",
    "Mars":    "Марс",
    "Jupiter": "Юпитер",
    "Saturn":  "Сатурн",
    "Uranus":  "Уран",
    "Neptune": "Нептун",
    "Pluto":   "Плутон",
    "True_Node": "Северный узел",
    "Chiron":  "Хирон",
}

ASPECT_NAMES_RU = {
    "conjunction":  "соединение",
    "opposition":   "оппозиция",
    "trine":        "тригон",
    "square":       "квадратура",
    "sextile":      "секстиль",
    "quincunx":     "квинконс",
    "semi-square":  "полуквадрат",
    "sesquiquadrate": "сесквиквадрат",
}

ASPECT_NATURE = {
    "conjunction": "нейтральный",
    "opposition":  "напряжённый",
    "trine":       "гармоничный",
    "square":      "напряжённый",
    "sextile":     "гармоничный",
    "quincunx":    "напряжённый",
}


@dataclass
class GeoResult:
    latitude: float
    longitude: float
    timezone_str: str
    city: str


@dataclass
class PlanetData:
    name: str
    name_ru: str
    sign: str
    sign_ru: str
    sign_symbol: str
    degree: float
    retrograde: bool


@dataclass
class AspectData:
    planet1: str
    planet2: str
    aspect: str
    aspect_ru: str
    nature: str
    orbit: float


@dataclass
class NatalChart:
    sun: PlanetData
    moon: PlanetData
    ascendant: str
    ascendant_ru: str
    ascendant_symbol: str
    planets: list[PlanetData]
    houses: list[dict]


@dataclass
class AstroReport:
    natal: NatalChart
    transits: list[PlanetData]
    transit_aspects: list[AspectData]
    natal_aspects: list[AspectData]
    week_start: str
    week_end: str


# ─── Геокодирование ──────────────────────────────────────────────────────────

def geocode_city(city: str) -> GeoResult:
    """Определяет координаты и часовой пояс города."""
    geolocator = Nominatim(user_agent=GEOPY_USER_AGENT)
    location = geolocator.geocode(city, language="ru", exactly_one=True, timeout=10)
    if not location:
        raise ValueError(f"Город не найден: {city}")

    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if not tz_str:
        tz_str = "UTC"

    return GeoResult(
        latitude=location.latitude,
        longitude=location.longitude,
        timezone_str=tz_str,
        city=location.address.split(",")[0].strip(),
    )


# ─── Парсинг планеты из объекта kerykeion ────────────────────────────────────

def _parse_planet(point) -> PlanetData:
    sign_key = point.sign if hasattr(point, "sign") else ""
    return PlanetData(
        name=point.name,
        name_ru=PLANET_NAMES_RU.get(point.name, point.name),
        sign=sign_key,
        sign_ru=SIGN_NAMES_RU.get(sign_key, sign_key),
        sign_symbol=SIGN_SYMBOLS.get(sign_key, ""),
        degree=round(point.position, 2),
        retrograde=getattr(point, "retrograde", False),
    )


# ─── Главная функция ─────────────────────────────────────────────────────────

def build_astro_report(
    birth_date: str,   # "DD.MM.YYYY"
    birth_time: str,   # "HH:MM"
    city: str,
) -> AstroReport:
    """
    Строит полный астрологический отчёт:
    натальная карта + текущие транзиты + аспекты.
    """

    # 1. Разбор даты и времени
    dt = datetime.strptime(f"{birth_date} {birth_time}", "%d.%m.%Y %H:%M")

    # 2. Геокодирование
    geo = geocode_city(city)

    # 3. Натальная карта
    natal_subject = AstrologicalSubject(
        name="User",
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        city=geo.city,
        lat=geo.latitude,
        lng=geo.longitude,
        tz_str=geo.timezone_str,
        zodiac_type="Tropic",
        online=False,
    )

    # Планеты натальной карты
    natal_planets_raw = [
        natal_subject.sun, natal_subject.moon, natal_subject.mercury,
        natal_subject.venus, natal_subject.mars, natal_subject.jupiter,
        natal_subject.saturn, natal_subject.uranus, natal_subject.neptune,
        natal_subject.pluto,
    ]
    natal_planets = [_parse_planet(p) for p in natal_planets_raw]

    # Натальная карта
    asc_sign = natal_subject.first_house.sign
    natal_chart = NatalChart(
        sun=_parse_planet(natal_subject.sun),
        moon=_parse_planet(natal_subject.moon),
        ascendant=asc_sign,
        ascendant_ru=SIGN_NAMES_RU.get(asc_sign, asc_sign),
        ascendant_symbol=SIGN_SYMBOLS.get(asc_sign, ""),
        planets=natal_planets,
        houses=[
            {
                "number": i + 1,
                "sign": house.sign,
                "sign_ru": SIGN_NAMES_RU.get(house.sign, house.sign),
                "degree": round(house.position, 2),
            }
            for i, house in enumerate([
                natal_subject.first_house, natal_subject.second_house,
                natal_subject.third_house, natal_subject.fourth_house,
                natal_subject.fifth_house, natal_subject.sixth_house,
                natal_subject.seventh_house, natal_subject.eighth_house,
                natal_subject.ninth_house, natal_subject.tenth_house,
                natal_subject.eleventh_house, natal_subject.twelfth_house,
            ])
        ],
    )

    # 4. Натальные аспекты
    natal_aspects_obj = NatalAspects(natal_subject)
    natal_aspects = []
    for asp in natal_aspects_obj.relevant_aspects:
        nature = ASPECT_NATURE.get(asp["aspect"], "нейтральный")
        natal_aspects.append(AspectData(
            planet1=PLANET_NAMES_RU.get(asp["p1_name"], asp["p1_name"]),
            planet2=PLANET_NAMES_RU.get(asp["p2_name"], asp["p2_name"]),
            aspect=asp["aspect"],
            aspect_ru=ASPECT_NAMES_RU.get(asp["aspect"], asp["aspect"]),
            nature=nature,
            orbit=round(asp["orbit"], 2),
        ))

    # 5. Текущие транзиты (положение планет сейчас)
    now = datetime.now(timezone.utc)
    transit_subject = AstrologicalSubject(
        name="Transit",
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        city="London",
        lat=51.5074,
        lng=-0.1278,
        tz_str="UTC",
        zodiac_type="Tropic",
        online=False,
    )

    transit_planets_raw = [
        transit_subject.sun, transit_subject.moon, transit_subject.mercury,
        transit_subject.venus, transit_subject.mars, transit_subject.jupiter,
        transit_subject.saturn, transit_subject.uranus, transit_subject.neptune,
        transit_subject.pluto,
    ]
    current_transits = [_parse_planet(p) for p in transit_planets_raw]

    # 6. Аспекты транзитных планет к натальным
    synastry = SynastryAspects(transit_subject, natal_subject)
    transit_aspects = []
    for asp in synastry.relevant_aspects:
        nature = ASPECT_NATURE.get(asp["aspect"], "нейтральный")
        transit_aspects.append(AspectData(
            planet1=f"тр. {PLANET_NAMES_RU.get(asp['p1_name'], asp['p1_name'])}",
            planet2=PLANET_NAMES_RU.get(asp["p2_name"], asp["p2_name"]),
            aspect=asp["aspect"],
            aspect_ru=ASPECT_NAMES_RU.get(asp["aspect"], asp["aspect"]),
            nature=nature,
            orbit=round(asp["orbit"], 2),
        ))

    # 7. Диапазон недели
    from datetime import timedelta
    today = now.date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return AstroReport(
        natal=natal_chart,
        transits=current_transits,
        transit_aspects=transit_aspects,
        natal_aspects=natal_aspects,
        week_start=monday.strftime("%d.%m.%Y"),
        week_end=sunday.strftime("%d.%m.%Y"),
    )
