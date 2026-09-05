from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
import datetime as dt
import pytz
import ephem
import math
import urllib.parse
import urllib.request
import json
import os
import re

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIG
# ============================================================

IST = pytz.timezone("Asia/Kolkata")

DEFAULT_CITY = "Ujjain"
DEFAULT_LAT = 23.1765
DEFAULT_LON = 75.7885

RASHI_NAMES = [
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
]

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वा फाल्गुनी",
    "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा",
    "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा",
    "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद",
    "उत्तरा भाद्रपद", "रेवती"
]

TITHI_NAMES = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

YOGA_NAMES = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन",
    "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि",
    "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात",
    "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ", "शुक्ल",
    "ब्रह्म", "ऐन्द्र", "वैधृति"
]

KARANA_FIXED = {
    0: "किंस्तुघ्न",
    57: "शकुनि",
    58: "चतुष्पाद",
    59: "नाग"
}

KARANA_MOVING = [
    "बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि"
]

WEEKDAYS = [
    "सोमवार", "मंगलवार", "बुधवार",
    "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"
]

PLANET_IDS = {
    "सूर्य": swe.SUN,
    "चंद्र": swe.MOON,
    "मंगल": swe.MARS,
    "बुध": swe.MERCURY,
    "गुरु": swe.JUPITER,
    "शुक्र": swe.VENUS,
    "शनि": swe.SATURN,
    "राहु": swe.MEAN_NODE
}

RASHI_LORDS = [
    "मंगल", "शुक्र", "बुध", "चंद्र",
    "सूर्य", "बुध", "शुक्र", "मंगल",
    "गुरु", "शनि", "शनि", "गुरु"
]

DASHA_YEARS = {
    "केतु": 7.0,
    "शुक्र": 20.0,
    "सूर्य": 6.0,
    "चंद्र": 10.0,
    "मंगल": 7.0,
    "राहु": 18.0,
    "गुरु": 16.0,
    "शनि": 19.0,
    "बुध": 17.0
}

DASHA_ORDER = [
    "केतु", "शुक्र", "सूर्य", "चंद्र",
    "मंगल", "राहु", "गुरु", "शनि", "बुध"
]

NAKSHATRA_LORDS = [
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"
]

YONI = [
    "अश्व", "गज", "मेष", "सर्प", "सर्प", "श्वान", "मार्जार",
    "मेष", "मार्जार", "मूषक", "मूषक", "गौ", "महिष", "व्याघ्र",
    "महिष", "व्याघ्र", "मृग", "मृग", "श्वान", "वानर", "नकुल",
    "वानर", "अश्व", "गज", "अश्व", "सिंह", "गौ"
]

GANA = [
    "देव", "मनुष्य", "राक्षस", "मनुष्य", "देव", "मनुष्य", "देव",
    "देव", "राक्षस", "राक्षस", "मनुष्य", "मनुष्य", "देव", "राक्षस",
    "देव", "राक्षस", "देव", "राक्षस", "राक्षस", "मनुष्य", "मनुष्य",
    "देव", "राक्षस", "राक्षस", "मनुष्य", "मनुष्य", "देव"
]

NADI = [
    "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि", "मध्य",
    "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि", "मध्य", "अन्त्य",
    "अन्त्य", "मध्य", "आदि", "आदि", "मध्य", "अन्त्य", "अन्त्य",
    "मध्य", "आदि", "आदि", "मध्य", "अन्त्य"
]

VARNA_BY_RASHI = {
    0: "क्षत्रिय", 1: "वैश्य", 2: "शूद्र", 3: "ब्राह्मण",
    4: "क्षत्रिय", 5: "वैश्य", 6: "शूद्र", 7: "ब्राह्मण",
    8: "क्षत्रिय", 9: "वैश्य", 10: "शूद्र", 11: "ब्राह्मण"
}

# ============================================================
# 22 MUHURT CATEGORIES
#
# IMPORTANT:
# Vivah and Griha Pravesh are intentionally NOT included.
# ============================================================

MUHURT_TYPES = {
    "prasuta_snana": {
        "name": "प्रसूता स्नान / प्रथम स्नान मुहूर्त",
        "birth_required": True
    },
    "yatra": {
        "name": "यात्रा मुहूर्त",
        "birth_required": False,
        "extra": ["start_place", "destination"]
    },
    "havan": {
        "name": "हवन मुहूर्त",
        "birth_required": False
    },
    "puja": {
        "name": "पूजा / धार्मिक अनुष्ठान मुहूर्त",
        "birth_required": False,
        "extra": ["purpose"]
    },
    "vehicle_purchase": {
        "name": "नवीन वाहन खरीद मुहूर्त",
        "birth_required": False,
        "extra": ["vehicle_type"]
    },
    "vehicle_puja": {
        "name": "वाहन पूजन मुहूर्त",
        "birth_required": False,
        "extra": ["vehicle_type"]
    },
    "house_land_purchase": {
        "name": "नया घर / भूमि खरीद मुहूर्त",
        "birth_required": False
    },
    "land_puja": {
        "name": "भूमि पूजन मुहूर्त",
        "birth_required": False
    },
    "business_start": {
        "name": "नया व्यवसाय / व्यापार आरंभ मुहूर्त",
        "birth_required": True,
        "extra": ["business_type"]
    },
    "shop_office_opening": {
        "name": "दुकान / कार्यालय उद्घाटन मुहूर्त",
        "birth_required": True
    },
    "job_start": {
        "name": "नौकरी / कार्य आरंभ मुहूर्त",
        "birth_required": True
    },
    "engagement_roka": {
        "name": "सगाई / रोका मुहूर्त",
        "birth_required": True
    },
    "naming": {
        "name": "नामकरण मुहूर्त",
        "birth_required": True
    },
    "annaprashan": {
        "name": "अन्नप्राशन मुहूर्त",
        "birth_required": True
    },
    "mundan": {
        "name": "मुंडन मुहूर्त",
        "birth_required": True
    },
    "upanayana": {
        "name": "उपनयन / जनेऊ मुहूर्त",
        "birth_required": True
    },
    "vidyarambha": {
        "name": "विद्यारंभ मुहूर्त",
        "birth_required": True
    },
    "new_goods": {
        "name": "नया सामान / इलेक्ट्रॉनिक वस्तु खरीद मुहूर्त",
        "birth_required": False,
        "extra": ["item_type"]
    },
    "jewellery": {
        "name": "आभूषण खरीद मुहूर्त",
        "birth_required": False
    },
    "documents_contract": {
        "name": "दस्तावेज / अनुबंध मुहूर्त",
        "birth_required": False,
        "extra": ["document_type"]
    },
    "general_auspicious": {
        "name": "सामान्य शुभ कार्य मुहूर्त",
        "birth_required": False,
        "extra": ["purpose"]
    },
    "other": {
        "name": "अन्य शुभ कार्य",
        "birth_required": False,
        "extra": ["purpose"]
    }
}

# ============================================================
# MUHURT RULES
#
# Tithis are zero-based internally:
# 1 = प्रतिपदा, 2 = द्वितीया ... 15 = पूर्णिमा
# 16 = कृष्ण प्रतिपदा ... 30 = अमावस्या
#
# "preferred" gives positive scoring.
# "avoid" is a hard rejection where appropriate.
# ============================================================

RULES = {

    "prasuta_snana": {
        "avoid_tithi": [4, 6, 8, 9, 12, 14, 21, 23, 26, 28],
        "good_weekdays": [1, 2, 5, 6],
        "good_nakshatra": [
            0, 3, 4, 11, 12, 14, 16, 20, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 8, 11],
        "moon_personal": True
    },

    "yatra": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 1, 2, 3, 4, 6],
        "good_nakshatra": [
            0, 3, 4, 6, 7, 12, 14, 16, 20, 21, 25, 26
        ],
        "moon_personal": True
    },

    "havan": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 2, 3, 4, 6],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 13, 14, 16, 20, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 8, 11],
        "moon_personal": True
    },

    "puja": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 2, 3, 4, 6],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 13, 14, 16, 20, 25, 26
        ],
        "moon_personal": True
    },

    "vehicle_purchase": {
        "avoid_weekdays": [1, 5],
        "good_weekdays": [0, 2, 3, 4, 6],
        "avoid_tithi": [4, 9, 14, 30],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 14, 16, 20, 21, 25, 26
        ],
        "moon_personal": True
    },

    "vehicle_puja": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 2, 3, 4, 6],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 14, 16, 20, 25, 26
        ],
        "moon_personal": True
    },

    "house_land_purchase": {
        "avoid_tithi": [4, 9, 14, 15, 30],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            3, 4, 7, 12, 13, 16, 20, 25, 26
        ],
        "good_lagna": [1, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "land_puja": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            3, 4, 7, 12, 13, 16, 20, 25, 26
        ],
        "good_lagna": [1, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "business_start": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [2, 3, 4],
        "good_nakshatra": [
            3, 7, 12, 13, 14, 16, 25, 26
        ],
        "good_lagna": [1, 2, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "shop_office_opening": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [2, 3, 4],
        "good_nakshatra": [
            3, 7, 12, 13, 14, 16, 25, 26
        ],
        "good_lagna": [1, 2, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "job_start": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 13, 14, 16, 25, 26
        ],
        "good_lagna": [1, 2, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "engagement_roka": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            3, 4, 7, 12, 16, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "naming": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            0, 3, 4, 6, 7, 12, 13, 16, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "annaprashan": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            3, 4, 7, 12, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "mundan": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            0, 4, 6, 7, 12, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "upanayana": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 13, 16, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "vidyarambha": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [2, 3],
        "good_nakshatra": [
            0, 7, 12, 13, 25, 26
        ],
        "good_lagna": [1, 2, 3, 5, 6, 7, 8, 11],
        "moon_personal": True
    },

    "new_goods": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            3, 7, 12, 13, 14, 25, 26
        ],
        "moon_personal": True
    },

    "jewellery": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_weekdays": [0, 2, 3, 4],
        "good_nakshatra": [
            3, 7, 12, 25, 26
        ],
        "moon_personal": True
    },

    "documents_contract": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 10, 11, 12, 13],
        "good_weekdays": [2, 3, 4],
        "good_nakshatra": [
            7, 12, 13, 16, 25, 26
        ],
        "moon_personal": True
    },

    "general_auspicious": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4, 6],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 13, 14, 16, 25, 26
        ],
        "moon_personal": True
    },

    "other": {
        "avoid_tithi": [4, 9, 14, 30],
        "good_tithi": [2, 3, 5, 7, 10, 11, 12, 13],
        "good_weekdays": [0, 2, 3, 4, 6],
        "good_nakshatra": [
            0, 3, 4, 7, 12, 13, 14, 16, 25, 26
        ],
        "moon_personal": True
    }
}


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize(deg):
    return deg % 360.0


def parse_date_time(date_str, time_str):
    if not date_str:
        raise ValueError("Date is required")

    if not time_str:
        raise ValueError("Time is required")

    y, m, d = map(int, str(date_str).split("-"))

    parts = str(time_str).split(":")
    hh = int(parts[0])
    mm = int(parts[1]) if len(parts) > 1 else 0
    ss = int(parts[2]) if len(parts) > 2 else 0

    return IST.localize(
        dt.datetime(y, m, d, hh, mm, ss)
    )


def parse_location(source):
    city = source.get("city") or DEFAULT_CITY

    try:
        lat = float(source.get("lat", DEFAULT_LAT))
        lon = float(source.get("lon", DEFAULT_LON))
    except (TypeError, ValueError):
        lat = DEFAULT_LAT
        lon = DEFAULT_LON

    return city, lat, lon


def get_julian_day(local_dt):
    utc_dt = local_dt.astimezone(pytz.utc)

    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour
        + utc_dt.minute / 60.0
        + utc_dt.second / 3600.0
    )


def sidereal_position(jd, planet_id, with_speed=True):
    flags = swe.FLG_SIDEREAL

    if with_speed:
        flags |= swe.FLG_SPEED

    pos, _ = swe.calc_ut(
        jd,
        planet_id,
        flags
    )

    return normalize(pos[0]), pos[3]


def rashi_index(lon):
    return int(normalize(lon) / 30.0) % 12


def degree_text(lon):
    local = normalize(lon) % 30.0

    deg = int(local)

    minute_float = (local - deg) * 60.0

    minute = int(minute_float)

    second = int(
        round(
            (minute_float - minute) * 60
        )
    )

    if second >= 60:
        second = 0
        minute += 1

    if minute >= 60:
        minute = 0
        deg += 1

    return f"{deg}°{minute:02d}'{second:02d}\""


def nakshatra_info(lon):
    span = 360.0 / 27.0

    idx = min(
        26,
        int(normalize(lon) / span)
    )

    within = (
        normalize(lon)
        - idx * span
    )

    pada = min(
        4,
        int(within / (span / 4.0)) + 1
    )

    return (
        idx,
        NAKSHATRA_NAMES[idx],
        pada,
        NAKSHATRA_LORDS[idx]
    )


def karana_name(index):
    if index in KARANA_FIXED:
        return KARANA_FIXED[index]

    if 1 <= index <= 56:
        return KARANA_MOVING[
            (index - 1) % 7
        ]

    return "--"


def safe_date_text(value):
    return value.strftime("%d-%m-%Y")


# ============================================================
# SUN / MOON EVENTS
# ============================================================

def find_sun_event(
    y,
    m,
    d,
    lat,
    lon,
    rising=True
):
    observer = ephem.Observer()

    observer.lat = str(lat)
    observer.lon = str(lon)

    observer.date = (
        IST.localize(
            dt.datetime(y, m, d, 0, 5)
        )
        .astimezone(pytz.utc)
    )

    sun = ephem.Sun()

    try:
        value = (
            observer.next_rising(sun)
            if rising
            else observer.next_setting(sun)
        )

        value_dt = value.datetime()

        if value_dt.tzinfo is None:
            value_dt = pytz.utc.localize(
                value_dt
            )

        return value_dt.astimezone(IST)

    except Exception:
        return None


def moon_event(
    y,
    m,
    d,
    lat,
    lon,
    rising=True
):
    observer = ephem.Observer()

    observer.lat = str(lat)
    observer.lon = str(lon)

    observer.date = (
        IST.localize(
            dt.datetime(y, m, d, 0, 5)
        )
        .astimezone(pytz.utc)
    )

    moon = ephem.Moon()

    try:
        value = (
            observer.next_rising(moon)
            if rising
            else observer.next_setting(moon)
        )

        value_dt = value.datetime()

        if value_dt.tzinfo is None:
            value_dt = pytz.utc.localize(
                value_dt
            )

        return value_dt.astimezone(IST)

    except Exception:
        return None


# ============================================================
# PANCHANG CORE
# ============================================================

def tithi_at(jd):
    sun_lon, sun_speed = sidereal_position(
        jd, swe.SUN
    )

    moon_lon, moon_speed = sidereal_position(
        jd, swe.MOON
    )

    angle = normalize(
        moon_lon - sun_lon
    )

    idx = min(
        29,
        int(angle / 12.0)
    )

    return (
        idx,
        moon_lon,
        sun_lon,
        moon_speed,
        sun_speed
    )


def current_panchang(
    local_dt,
    city,
    lat,
    lon
):
    jd = get_julian_day(local_dt)

    (
        tithi_idx,
        moon_lon,
        sun_lon,
        moon_speed,
        sun_speed
    ) = tithi_at(jd)

    nak_idx, nak_name, nak_pada, nak_lord = (
        nakshatra_info(moon_lon)
    )

    yoga_idx = int(
        normalize(
            sun_lon + moon_lon
        )
        / (360.0 / 27.0)
    )

    yoga_idx = min(
        26,
        yoga_idx
    )

    karana_idx = int(
        normalize(
            moon_lon - sun_lon
        ) / 6.0
    )

    sun_rashi = rashi_index(
        sun_lon
    )

    moon_rashi = rashi_index(
        moon_lon
    )

    return {
        "tithi_index": tithi_idx + 1,
        "tithi": TITHI_NAMES[tithi_idx],
        "paksha": (
            "शुक्ल पक्ष"
            if tithi_idx < 15
            else "कृष्ण पक्ष"
        ),
        "nakshatra_index": nak_idx,
        "nakshatra": nak_name,
        "nakshatra_pada": nak_pada,
        "nakshatra_lord": nak_lord,
        "yoga": YOGA_NAMES[yoga_idx],
        "yoga_index": yoga_idx + 1,
        "karana": karana_name(karana_idx),
        "chandra_rashi": RASHI_NAMES[moon_rashi],
        "chandra_rashi_num": moon_rashi + 1,
        "surya_rashi": RASHI_NAMES[sun_rashi],
        "moon_longitude": round(
            moon_lon,
            6
        ),
        "sun_longitude": round(
            sun_lon,
            6
        )
    }


# ============================================================
# LAGNA
# ============================================================

def calculate_lagna(local_dt, lat, lon):
    jd = get_julian_day(local_dt)

    swe.set_sid_mode(
        swe.SIDM_LAHIRI
    )

    try:
        cusps, ascmc = swe.houses_ex(
            jd,
            lat,
            lon,
            b"P",
            swe.FLG_SIDEREAL
        )

        asc = normalize(
            ascmc[0]
        )

    except Exception:
        cusps, ascmc = swe.houses(
            jd,
            lat,
            lon,
            b"P"
        )

        ayan = swe.get_ayanamsa_ut(
            jd
        )

        asc = normalize(
            ascmc[0] - ayan
        )

    idx = rashi_index(
        asc
    )

    return {
        "longitude": round(
            asc,
            6
        ),
        "rashi_index": idx,
        "rashi_num": idx + 1,
        "rashi": RASHI_NAMES[idx],
        "degree": degree_text(asc)
    }


# ============================================================
# BIRTH MOON
# ============================================================

def get_birth_moon_rashi(data):
    date_value = (
        data.get("birth_date")
        or data.get("dob")
    )

    time_value = (
        data.get("birth_time")
        or data.get("time")
    )

    if not date_value or not time_value:
        return None

    try:
        birth_dt = parse_date_time(
            date_value,
            time_value
        )

        jd = get_julian_day(
            birth_dt
        )

        moon_lon, _ = sidereal_position(
            jd,
            swe.MOON
        )

        return rashi_index(
            moon_lon
        )

    except Exception:
        return None


def moon_distance_from_birth(
    birth_rashi,
    muhurat_rashi
):
    if birth_rashi is None:
        return None

    return (
        (
            muhurat_rashi
            - birth_rashi
            + 12
        )
        % 12
    ) + 1


# ============================================================
# FINAL USER MOON RULE
#
# MUHURAT MOON MUST NOT BE:
# 4th, 8th or 12th from birth Moon.
# ============================================================

def moon_rule_passes(
    birth_rashi,
    muhurat_rashi
):
    distance = moon_distance_from_birth(
        birth_rashi,
        muhurat_rashi
    )

    if distance is None:
        return True, None

    if distance in [4, 8, 12]:
        return False, distance

    return True, distance


# ============================================================
# TIME INTERVAL HELPERS
# ============================================================

def combine_date_time(
    date_obj,
    minutes
):
    return IST.localize(
        dt.datetime(
            date_obj.year,
            date_obj.month,
            date_obj.day
        )
    ) + dt.timedelta(
        minutes=minutes
    )


def interval_overlap(
    a_start,
    a_end,
    b_start,
    b_end
):
    start = max(
        a_start,
        b_start
    )

    end = min(
        a_end,
        b_end
    )

    if start < end:
        return start, end

    return None


def subtract_interval(
    intervals,
    blocked_start,
    blocked_end
):
    result = []

    for start, end in intervals:

        if blocked_end <= start:
            result.append(
                (start, end)
            )
            continue

        if blocked_start >= end:
            result.append(
                (start, end)
            )
            continue

        if start < blocked_start:
            result.append(
                (start, blocked_start)
            )

        if blocked_end < end:
            result.append(
                (blocked_end, end)
            )

    return result


def fmt_time(value):
    return value.strftime(
        "%I:%M %p"
    ).lstrip("0")


def duration_minutes(
    start,
    end
):
    return int(
        (end - start).total_seconds()
        / 60
    )


# ============================================================
# RAHU / YAMAGANDA / GULIKA
# ============================================================

# Traditional day-segment positions.
#
# Rahu:
# Sunday 8
# Monday 2
# Tuesday 7
# Wednesday 5
# Thursday 6
# Friday 4
# Saturday 3
#
# Yamaganda:
# Sunday 5
# Monday 4
# Tuesday 3
# Wednesday 2
# Thursday 1
# Friday 7
# Saturday 6
#
# Gulika:
# Sunday 7
# Monday 6
# Tuesday 5
# Wednesday 4
# Thursday 3
# Friday 2
# Saturday 1

RAHU_SEGMENT = [
    8, 2, 7, 5, 6, 4, 3
]

YAMA_SEGMENT = [
    5, 4, 3, 2, 1, 7, 6
]

GULIKA_SEGMENT = [
    7, 6, 5, 4, 3, 2, 1
]


def day_segments(
    sunrise,
    sunset
):
    total = (
        sunset - sunrise
    ).total_seconds() / 8.0

    result = []

    for i in range(8):
        start = (
            sunrise
            + dt.timedelta(
                seconds=total * i
            )
        )

        end = (
            sunrise
            + dt.timedelta(
                seconds=total * (i + 1)
            )
        )

        result.append(
            (start, end)
        )

    return result


def daytime_dosha_intervals(
    date_obj,
    lat,
    lon
):
    sunrise = find_sun_event(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        lat,
        lon,
        True
    )

    sunset = find_sun_event(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        lat,
        lon,
        False
    )

    if not sunrise or not sunset:
        return [], sunrise, sunset

    segments = day_segments(
        sunrise,
        sunset
    )

    weekday = date_obj.weekday()

    result = []

    r = RAHU_SEGMENT[weekday] - 1
    y = YAMA_SEGMENT[weekday] - 1
    g = GULIKA_SEGMENT[weekday] - 1

    result.append(
        (
            segments[r][0],
            segments[r][1],
            "राहुकाल"
        )
    )

    result.append(
        (
            segments[y][0],
            segments[y][1],
            "यमगण्ड"
        )
    )

    result.append(
        (
            segments[g][0],
            segments[g][1],
            "गुलिक काल"
        )
    )

    return result, sunrise, sunset


# ============================================================
# APPROXIMATE DURMUHURTA
#
# Used as a time exclusion only.
# ============================================================

def durmuhurta_intervals(
    sunrise,
    sunset
):
    if not sunrise or not sunset:
        return []

    day_length = (
        sunset - sunrise
    ).total_seconds()

    # Traditional daytime muhurt subdivision:
    # one daytime muhurta = day length / 15
    muhurta = day_length / 15.0

    # General daily Durmuhurta windows.
    # Kept configurable here.
    a_start = (
        sunrise
        + dt.timedelta(
            seconds=muhurta * 3
        )
    )

    a_end = (
        a_start
        + dt.timedelta(
            seconds=muhurta
        )
    )

    b_start = (
        sunrise
        + dt.timedelta(
            seconds=muhurta * 7
        )
    )

    b_end = (
        b_start
        + dt.timedelta(
            seconds=muhurta
        )
    )

    return [
        (
            a_start,
            a_end,
            "दुर्मुहूर्त"
        ),
        (
            b_start,
            b_end,
            "दुर्मुहूर्त"
        )
    ]


# ============================================================
# CANDIDATE TIME GRID
# ============================================================

def daylight_grid(
    date_obj,
    lat,
    lon
):
    sunrise = find_sun_event(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        lat,
        lon,
        True
    )

    sunset = find_sun_event(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        lat,
        lon,
        False
    )

    if not sunrise or not sunset:
        return []

    result = []

    cursor = sunrise

    while cursor < sunset:
        end = min(
            cursor
            + dt.timedelta(
                minutes=10
            ),
            sunset
        )

        result.append(
            (cursor, end)
        )

        cursor = end

    return result


# ============================================================
# FIND TITHI / NAKSHATRA / LAGNA AT EXACT TIME
# ============================================================

def calculate_candidate(
    when,
    city,
    lat,
    lon
):
    p = current_panchang(
        when,
        city,
        lat,
        lon
    )

    lagna = calculate_lagna(
        when,
        lat,
        lon
    )

    return {
        **p,
        "lagna": lagna,
        "weekday_index": when.weekday(),
        "weekday": WEEKDAYS[
            when.weekday()
        ],
        "date": when.strftime(
            "%Y-%m-%d"
        ),
        "time": fmt_time(
            when
        )
    }


# ============================================================
# RULE EVALUATION
# ============================================================

def evaluate_candidate(
    candidate,
    rule,
    birth_rashi=None
):
    score = 0
    reasons = []
    failures = []

    tithi = candidate[
        "tithi_index"
    ]

    weekday = candidate[
        "weekday_index"
    ]

    nak = candidate[
        "nakshatra_index"
    ]

    lagna = candidate[
        "lagna"
    ]["rashi_num"] - 1

    # --------------------------------------------------------
    # HARD TITHI
    # --------------------------------------------------------

    if tithi in rule.get(
        "avoid_tithi",
        []
    ):
        failures.append(
            f"तिथि {candidate['tithi']} निषिद्ध"
        )

    # --------------------------------------------------------
    # PREFERRED TITHI
    # --------------------------------------------------------

    if tithi in rule.get(
        "good_tithi",
        []
    ):
        score += 25
        reasons.append(
            "शुभ तिथि"
        )

    # --------------------------------------------------------
    # WEEKDAY
    # --------------------------------------------------------

    if weekday in rule.get(
        "avoid_weekdays",
        []
    ):
        failures.append(
            f"{candidate['weekday']} निषिद्ध"
        )

    if weekday in rule.get(
        "good_weekdays",
        []
    ):
        score += 15
        reasons.append(
            "अनुकूल वार"
        )

    # --------------------------------------------------------
    # NAKSHATRA
    # --------------------------------------------------------

    if nak in rule.get(
        "good_nakshatra",
        []
    ):
        score += 30
        reasons.append(
            f"{candidate['nakshatra']} शुभ नक्षत्र"
        )

    # --------------------------------------------------------
    # LAGNA
    # --------------------------------------------------------

    if (
        "good_lagna" in rule
        and lagna in rule["good_lagna"]
    ):
        score += 20
        reasons.append(
            f"{candidate['lagna']['rashi']} लग्न अनुकूल"
        )

    # --------------------------------------------------------
    # PERSONAL MOON RULE
    #
    # ONLY 4 / 8 / 12 ARE REJECTED.
    # --------------------------------------------------------

    moon_distance = None

    if rule.get(
        "moon_personal",
        False
    ):
        passes, moon_distance = (
            moon_rule_passes(
                birth_rashi,
                candidate[
                    "chandra_rashi_num"
                ] - 1
            )
        )

        if birth_rashi is not None:

            if not passes:
                failures.append(
                    "जन्म राशि से चंद्रमा "
                    f"{moon_distance}वें स्थान में है "
                    "(4/8/12 निषिद्ध)"
                )

            else:
                score += 20

                reasons.append(
                    "जन्म राशि से चंद्रमा "
                    f"{moon_distance}वें स्थान में"
                )

    return {
        "score": score,
        "reasons": reasons,
        "failures": failures,
        "moon_distance": moon_distance
    }


# ============================================================
# FORBIDDEN TIME FILTER
# ============================================================

def apply_time_filters(
    intervals,
    date_obj,
    lat,
    lon
):
    doshas, sunrise, sunset = (
        daytime_dosha_intervals(
            date_obj,
            lat,
            lon
        )
    )

    dur = durmuhurta_intervals(
        sunrise,
        sunset
    )

    blocked = doshas + dur

    result = intervals

    removed = []

    for bs, be, name in blocked:

        before = list(result)

        result = subtract_interval(
            result,
            bs,
            be
        )

        if before != result:
            removed.append({
                "name": name,
                "start": fmt_time(bs),
                "end": fmt_time(be)
            })

    return result, removed, sunrise, sunset


# ============================================================
# SEARCH ONE DATE
# ============================================================

def search_one_date(
    date_obj,
    muhurt_type,
    city,
    lat,
    lon,
    birth_rashi=None
):
    rule = RULES.get(
        muhurt_type
    )

    if not rule:
        raise ValueError(
            "Unknown Muhurt type"
        )

    # --------------------------------------------------------
    # Check daytime
    # --------------------------------------------------------

    intervals = daylight_grid(
        date_obj,
        lat,
        lon
    )

    if not intervals:
        return []

    # --------------------------------------------------------
    # Remove forbidden periods
    # --------------------------------------------------------

    clean_intervals, removed, sunrise, sunset = (
        apply_time_filters(
            intervals,
            date_obj,
            lat,
            lon
        )
    )

    if not clean_intervals:
        return []

    # --------------------------------------------------------
    # Evaluate every 10-minute candidate
    # --------------------------------------------------------

    evaluated = []

    for start, end in clean_intervals:

        midpoint = (
            start
            + (
                end - start
            ) / 2
        )

        candidate = calculate_candidate(
            midpoint,
            city,
            lat,
            lon
        )

        evaluation = evaluate_candidate(
            candidate,
            rule,
            birth_rashi
        )

        if evaluation[
            "failures"
        ]:
            continue

        # ----------------------------------------------------
        # Additional quality score
        # ----------------------------------------------------

        local_score = evaluation[
            "score"
        ]

        # Strong Choghadiya-like preference:
        # daytime intervals are not declared blindly good.
        # This is only ranking.
        hour = midpoint.hour

        if 9 <= hour <= 12:
            local_score += 3

        if 13 <= hour <= 16:
            local_score += 2

        evaluated.append({
            "start": start,
            "end": end,
            "midpoint": midpoint,
            "candidate": candidate,
            "evaluation": evaluation,
            "score": local_score,
            "removed_periods": removed,
            "sunrise": sunrise,
            "sunset": sunset
        })

    return evaluated


# ============================================================
# MERGE ADJACENT GOOD INTERVALS
# ============================================================

def merge_results(results):
    if not results:
        return []

    results = sorted(
        results,
        key=lambda x: x["start"]
    )

    merged = []

    for item in results:

        if not merged:
            merged.append(
                item
            )
            continue

        previous = merged[-1]

        if (
            item["start"]
            <= previous["end"]
            + dt.timedelta(
                minutes=1
            )
        ):

            previous["end"] = max(
                previous["end"],
                item["end"]
            )

            previous["score"] = max(
                previous["score"],
                item["score"]
            )

        else:
            merged.append(
                item
            )

    return merged


# ============================================================
# FINAL RESULT FORMAT
# ============================================================

def format_muhurt_result(
    item,
    muhurt_type,
    birth_rashi=None
):
    midpoint = (
        item["start"]
        + (
            item["end"]
            - item["start"]
        ) / 2
    )

    data = calculate_candidate(
        midpoint,
        item.get("city", DEFAULT_CITY),
        item.get("lat", DEFAULT_LAT),
        item.get("lon", DEFAULT_LON)
    )

    moon_distance = item[
        "evaluation"
    ].get(
        "moon_distance"
    )

    return {
        "date": item[
            "start"
        ].strftime(
            "%d-%m-%Y"
        ),

        "date_iso": item[
            "start"
        ].strftime(
            "%Y-%m-%d"
        ),

        "start_time": fmt_time(
            item["start"]
        ),

        "end_time": fmt_time(
            item["end"]
        ),

        "duration_minutes": duration_minutes(
            item["start"],
            item["end"]
        ),

        "score": item[
            "score"
        ],

        "tithi": data[
            "tithi"
        ],

        "paksha": data[
            "paksha"
        ],

        "nakshatra": data[
            "nakshatra"
        ],

        "nakshatra_pada": data[
            "nakshatra_pada"
        ],

        "yoga": data[
            "yoga"
        ],

        "karana": data[
            "karana"
        ],

        "weekday": data[
            "weekday"
        ],

        "chandra_rashi": data[
            "chandra_rashi"
        ],

        "chandra_rashi_num": data[
            "chandra_rashi_num"
        ],

        "chandra_longitude": data[
            "moon_longitude"
        ],

        "lagna": data[
            "lagna"
        ],

        "moon_from_birth_rashi": (
            moon_distance
        ),

        "reasons": item[
            "evaluation"
        ]["reasons"],

        "removed_periods": item[
            "removed_periods"
        ],

        "sunrise": (
            fmt_time(
                item["sunrise"]
            )
            if item.get("sunrise")
            else "--"
        ),

        "sunset": (
            fmt_time(
                item["sunset"]
            )
            if item.get("sunset")
            else "--"
        )
    }


# ============================================================
# MUHURT SEARCH
# ============================================================

def search_muhurt(
    payload
):
    muhurt_type = (
        payload.get(
            "muhurt_type"
        )
        or ""
    ).strip()

    if muhurt_type not in MUHURT_TYPES:
        raise ValueError(
            "Invalid muhurt_type"
        )

    city, lat, lon = parse_location(
        payload
    )

    from_date = (
        payload.get(
            "from_date"
        )
        or payload.get(
            "date"
        )
    )

    if not from_date:
        raise ValueError(
            "from_date is required"
        )

    try:
        start_date = dt.datetime.strptime(
            from_date,
            "%Y-%m-%d"
        ).date()

    except Exception:
        raise ValueError(
            "from_date must be YYYY-MM-DD"
        )

    try:
        days = int(
            payload.get(
                "days",
                15
            )
        )

    except Exception:
        days = 15

    days = max(
        1,
        min(
            days,
            90
        )
    )

    # --------------------------------------------------------
    # Birth Moon
    # --------------------------------------------------------

    birth_rashi = get_birth_moon_rashi(
        payload
    )

    rule = RULES[
        muhurt_type
    ]

    all_results = []

    for offset in range(
        days
    ):
        date_obj = (
            start_date
            + dt.timedelta(
                days=offset
            )
        )

        daily = search_one_date(
            date_obj,
            muhurt_type,
            city,
            lat,
            lon,
            birth_rashi
        )

        for result in daily:
            result[
                "city"
            ] = city
            result[
                "lat"
            ] = lat
            result[
                "lon"
            ] = lon

        all_results.extend(
            daily
        )

    # --------------------------------------------------------
    # Merge continuous intervals
    # --------------------------------------------------------

    merged = merge_results(
        all_results
    )

    # --------------------------------------------------------
    # Minimum useful duration
    # --------------------------------------------------------

    merged = [
        x
        for x in merged
        if duration_minutes(
            x["start"],
            x["end"]
        ) >= 5
    ]

    merged.sort(
        key=lambda x: (
            -x["score"],
            x["start"]
        )
    )

    formatted = []

    for item in merged:
        formatted.append(
            format_muhurt_result(
                item,
                muhurt_type,
                birth_rashi
            )
        )

    # --------------------------------------------------------
    # Best result
    # --------------------------------------------------------

    best = (
        formatted[0]
        if formatted
        else None
    )

    alternatives = formatted[
        1:6
    ]

    # --------------------------------------------------------
    # Birth information
    # --------------------------------------------------------

    birth_info = None

    if birth_rashi is not None:
        birth_info = {
            "rashi_num": birth_rashi + 1,
            "rashi": RASHI_NAMES[
                birth_rashi
            ],
            "moon_rule": (
                "मुहूर्त चंद्रमा "
                "जन्म राशि से 4, 8 या 12 "
                "स्थान में नहीं होना चाहिए"
            )
        }

    return {
        "success": True,

        "muhurt": {
            "type": muhurt_type,
            "name": MUHURT_TYPES[
                muhurt_type
            ]["name"]
        },

        "search": {
            "from_date": from_date,
            "days": days,
            "to_date": (
                start_date
                + dt.timedelta(
                    days=days - 1
                )
            ).strftime(
                "%Y-%m-%d"
            )
        },

        "location": {
            "city": city,
            "latitude": lat,
            "longitude": lon
        },

        "birth": birth_info,

        "best_muhurt": best,

        "alternatives": alternatives,

        "total_found": len(
            formatted
        ),

        "rule_info": {
            "moon_restriction": (
                "4th, 8th, 12th"
            ),
            "excluded_categories": [
                "विवाह मुहूर्त",
                "गृह प्रवेश मुहूर्त"
            ]
        }
    }


# ============================================================
# PANCHANG API
# ============================================================

def panchang_for_date(
    date_str,
    city,
    lat,
    lon
):
    y, m, d = map(
        int,
        date_str.split("-")
    )

    local_dt = IST.localize(
        dt.datetime(
            y,
            m,
            d,
            12,
            0
        )
    )

    data = current_panchang(
        local_dt,
        city,
        lat,
        lon
    )

    sunrise = find_sun_event(
        y, m, d,
        lat, lon,
        True
    )

    sunset = find_sun_event(
        y, m, d,
        lat, lon,
        False
    )

    moonrise = moon_event(
        y, m, d,
        lat, lon,
        True
    )

    moonset = moon_event(
        y, m, d,
        lat, lon,
        False
    )

    return {
        "success": True,

        "data": {
            "location": {
                "city": city,
                "latitude": lat,
                "longitude": lon
            },

            "summary_header": (
                f"{data['tithi']}, "
                f"{data['nakshatra']} नक्षत्र"
            ),

            "details": {
                "tithi": data[
                    "tithi"
                ],

                "tithi_index": data[
                    "tithi_index"
                ],

                "paksha": data[
                    "paksha"
                ],

                "nakshatra": data[
                    "nakshatra"
                ],

                "nakshatra_pada": data[
                    "nakshatra_pada"
                ],

                "nakshatra_lord": data[
                    "nakshatra_lord"
                ],

                "yog": data[
                    "yoga"
                ],

                "karan_1": data[
                    "karana"
                ],

                "var": data[
                    "weekday"
                ],

                "chandra_rashi": data[
                    "chandra_rashi"
                ],

                "surya_rashi": data[
                    "surya_rashi"
                ],

                "moon_longitude": data[
                    "moon_longitude"
                ],

                "sun_longitude": data[
                    "sun_longitude"
                ]
            },

            "timings": {
                "sunrise": (
                    fmt_time(
                        sunrise
                    )
                    if sunrise
                    else "--"
                ),

                "sunset": (
                    fmt_time(
                        sunset
                    )
                    if sunset
                    else "--"
                ),

                "chandrodaya": (
                    fmt_time(
                        moonrise
                    )
                    if moonrise
                    else "--"
                ),

                "chandrast": (
                    fmt_time(
                        moonset
                    )
                    if moonset
                    else "--"
                )
            }
        }
    }


# ============================================================
# KUNDALI HELPERS
# ============================================================

def planet_record(
    name,
    lon,
    speed,
    sun_lon
):
    r_idx = rashi_index(
        lon
    )

    (
        n_idx,
        n_name,
        n_pada,
        n_lord
    ) = nakshatra_info(
        lon
    )

    is_asta = False

    if name not in [
        "सूर्य",
        "चंद्र",
        "राहु",
        "केतु"
    ]:

        diff = abs(
            lon - sun_lon
        )

        if diff > 180:
            diff = 360 - diff

        is_asta = (
            diff <= 8.5
        )

    return {
        "name": name,
        "longitude": round(
            lon,
            6
        ),
        "rashi": RASHI_NAMES[
            r_idx
        ],
        "rashi_num": r_idx + 1,
        "degree": degree_text(
            lon
        ),
        "nakshatra": n_name,
        "nakshatra_pada": n_pada,
        "nakshatra_lord": n_lord,
        "is_vakri": bool(
            speed < 0
        ),
        "is_asta": bool(
            is_asta
        )
    }


def calculate_houses(
    jd,
    lat,
    lon
):
    swe.set_sid_mode(
        swe.SIDM_LAHIRI
    )

    try:
        cusps, ascmc = swe.houses_ex(
            jd,
            lat,
            lon,
            b"P",
            swe.FLG_SIDEREAL
        )

        asc = normalize(
            ascmc[0]
        )

        cusp_list = [
            normalize(
                cusps[i]
            )
            for i in range(12)
        ]

        return asc, cusp_list

    except Exception:

        cusps, ascmc = swe.houses(
            jd,
            lat,
            lon,
            b"P"
        )

        ayan = swe.get_ayanamsa_ut(
            jd
        )

        asc = normalize(
            ascmc[0] - ayan
        )

        cusp_list = [
            normalize(
                c - ayan
            )
            for c in cusps[:12]
        ]

        return asc, cusp_list


def house_from_equal_whole_sign(
    lon,
    asc_lon
):
    return (
        (
            rashi_index(lon)
            - rashi_index(asc_lon)
        ) % 12
    ) + 1


def manglik_status(
    mars_rashi,
    asc_rashi
):
    house = (
        (
            mars_rashi
            - asc_rashi
        ) % 12
    ) + 1

    is_manglik = house in [
        1, 4, 7, 8, 12
    ]

    return {
        "is_manglik": is_manglik,
        "status": (
            "मांगलिक है"
            if is_manglik
            else "मांगलिक नहीं"
        ),
        "mars_house_from_lagna": house
    }


# ============================================================
# VIMSHOTTARI DASHA
# ============================================================

def add_years(
    base_date,
    years
):
    return base_date + dt.timedelta(
        days=years * 365.2425
    )


def dasha_sequence(
    start_lord
):
    idx = DASHA_ORDER.index(
        start_lord
    )

    return (
        DASHA_ORDER[idx:]
        + DASHA_ORDER[:idx]
    )


def build_antardashas(
    maha_lord,
    maha_start,
    maha_end,
    now
):
    total_days = (
        maha_end
        - maha_start
    ).total_seconds() / 86400.0

    result = []

    cursor = maha_start

    for lord in dasha_sequence(
        maha_lord
    ):

        duration_days = (
            total_days
            * DASHA_YEARS[lord]
            / 120.0
        )

        end = (
            cursor
            + dt.timedelta(
                days=duration_days
            )
        )

        result.append({
            "planet": lord,
            "start": cursor.strftime(
                "%d-%m-%Y"
            ),
            "end": end.strftime(
                "%d-%m-%Y"
            ),
            "current": (
                cursor <= now < end
            )
        })

        cursor = end

    return result


def calculate_vimshottari(
    dob_local,
    moon_lon
):
    (
        nak_idx,
        nak_name,
        pada,
        nak_lord
    ) = nakshatra_info(
        moon_lon
    )

    span = 360.0 / 27.0

    nak_start = (
        nak_idx * span
    )

    travelled = (
        normalize(moon_lon)
        - nak_start
    )

    fraction_completed = max(
        0.0,
        min(
            1.0,
            travelled / span
        )
    )

    first_lord = nak_lord

    first_years_remaining = (
        DASHA_YEARS[first_lord]
        * (
            1.0
            - fraction_completed
        )
    )

    cursor = dob_local

    now = dt.datetime.now(
        IST
    )

    mahadashas = []

    first = True

    while len(
        mahadashas
    ) < 18:

        if first:
            lord = first_lord
        else:
            lord = DASHA_ORDER[
                (
                    DASHA_ORDER.index(
                        first_lord
                    )
                    + len(mahadashas)
                ) % 9
            ]

        years = (
            first_years_remaining
            if first
            else DASHA_YEARS[lord]
        )

        end = add_years(
            cursor,
            years
        )

        mahadashas.append({
            "planet": lord,
            "start": cursor.strftime(
                "%d-%m-%Y"
            ),
            "end": end.strftime(
                "%d-%m-%Y"
            ),
            "years": round(
                years,
                4
            ),
            "current": (
                cursor <= now < end
            ),
            "antardasha":
                build_antardashas(
                    lord,
                    cursor,
                    end,
                    now
                )
        })

        cursor = end
        first = False

    current_maha = next(
        (
            x
            for x in mahadashas
            if x["current"]
        ),
        None
    )

    return {
        "nakshatra": nak_name,
        "nakshatra_pada": pada,
        "starting_mahadasha": first_lord,
        "current_mahadasha": (
            current_maha["planet"]
            if current_maha
            else None
        ),
        "mahadasha": mahadashas
    }


# ============================================================
# LOCATION SEARCH
# ============================================================

def location_search(
    query
):
    query = (
        query or ""
    ).strip()

    if not query:
        return []

    params = urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 8,
        "countrycodes": "in"
    })

    url = (
        "https://nominatim.openstreetmap.org/search?"
        + params
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "HindiPanchang-Kundali/1.0"
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=10
    ) as response:

        raw = response.read().decode(
            "utf-8"
        )

        items = json.loads(
            raw
        )

    result = []

    for item in items:

        address = item.get(
            "address",
            {}
        )

        result.append({
            "display_name":
                item.get(
                    "display_name",
                    ""
                ),

            "city": (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
                or ""
            ),

            "district":
                address.get(
                    "state_district",
                    ""
                ),

            "state":
                address.get(
                    "state",
                    ""
                ),

            "pincode":
                address.get(
                    "postcode",
                    ""
                ),

            "country":
                address.get(
                    "country",
                    ""
                ),

            "latitude":
                float(
                    item["lat"]
                ),

            "longitude":
                float(
                    item["lon"]
                )
        })

    return result


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():

    return jsonify({
        "success": True,
        "service":
            "Hindi Panchang & Kundali API",
        "status": "online",
        "version": "3.0",
        "endpoints": [
            "/health",

            "/api/full-panchang-hindi"
            "?date=YYYY-MM-DD"
            "&city=Ujjain"
            "&lat=23.1765"
            "&lon=75.7885",

            "/api/generate-kundali",

            "/api/dasha",

            "/api/location",

            "/api/muhurt"
        ],

        "muhurt_categories":
            len(MUHURT_TYPES),

        "excluded_categories": [
            "विवाह मुहूर्त",
            "गृह प्रवेश मुहूर्त"
        ]
    })


@app.get("/health")
def health():

    return jsonify({
        "success": True,
        "status": "healthy",
        "service":
            "Hindi Panchang & Kundali API",
        "version": "3.0"
    })


# ============================================================
# PANCHANG
# ============================================================

@app.get(
    "/api/full-panchang-hindi"
)
@app.get(
    "/api/full-panchang-hindi-fix"
)
def get_panchang():

    try:

        date_str = request.args.get(
            "date"
        )

        city, lat, lon = parse_location(
            request.args
        )

        if not date_str:
            return jsonify({
                "success": False,
                "error":
                    "Date is required"
            }), 400

        return jsonify(
            panchang_for_date(
                date_str,
                city,
                lat,
                lon
            )
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# KUNDALI
# ============================================================

@app.route(
    "/api/generate-kundali",
    methods=["GET", "POST"]
)
def generate_kundali():

    try:

        if request.method == "POST":
            data = (
                request.get_json(
                    silent=True
                )
                or {}
            )
        else:
            data = request.args

        date_str = (
            data.get("dob")
            or data.get("date")
        )

        time_str = data.get(
            "time"
        )

        name = data.get(
            "name",
            ""
        )

        city, lat, lon = parse_location(
            data
        )

        birth_dt = parse_date_time(
            date_str,
            time_str
        )

        jd = get_julian_day(
            birth_dt
        )

        swe.set_sid_mode(
            swe.SIDM_LAHIRI
        )

        sun_lon, _ = sidereal_position(
            jd,
            swe.SUN
        )

        moon_lon, _ = sidereal_position(
            jd,
            swe.MOON
        )

        planet_data = {}

        for name_key, p_id in PLANET_IDS.items():

            lon_value, speed = (
                sidereal_position(
                    jd,
                    p_id
                )
            )

            planet_data[
                name_key
            ] = planet_record(
                name_key,
                lon_value,
                speed,
                sun_lon
            )

        ketu_lon = normalize(
            planet_data[
                "राहु"
            ]["longitude"]
            + 180.0
        )

        planet_data[
            "केतु"
        ] = planet_record(
            "केतु",
            ketu_lon,
            -1.0,
            sun_lon
        )

        asc_lon, cusp_list = (
            calculate_houses(
                jd,
                lat,
                lon
            )
        )

        asc_rashi = rashi_index(
            asc_lon
        )

        houses = []

        for house_num in range(
            1,
            13
        ):

            sign_idx = (
                asc_rashi
                + house_num
                - 1
            ) % 12

            houses.append({
                "house":
                    house_num,

                "rashi":
                    RASHI_NAMES[
                        sign_idx
                    ],

                "rashi_num":
                    sign_idx + 1,

                "planets": []
            })

        for p_name, p in (
            planet_data.items()
        ):

            h = (
                house_from_equal_whole_sign(
                    p["longitude"],
                    asc_lon
                )
            )

            houses[
                h - 1
            ]["planets"].append({
                "name": p_name,
                "vakri":
                    p["is_vakri"],
                "asta":
                    p["is_asta"]
            })

            p["house"] = h

        (
            nak_idx,
            nak_name,
            nak_pada,
            nak_lord
        ) = nakshatra_info(
            moon_lon
        )

        moon_rashi = rashi_index(
            moon_lon
        )

        panchang = (
            panchang_for_date(
                date_str,
                city,
                lat,
                lon
            )["data"]
        )

        mars_rashi = rashi_index(
            planet_data[
                "मंगल"
            ]["longitude"]
        )

        manglik = manglik_status(
            mars_rashi,
            asc_rashi
        )

        birth_details = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "city": city,
            "latitude": lat,
            "longitude": lon
        }

        dasha = calculate_vimshottari(
            birth_dt,
            moon_lon
        )

        paya_map = {
            0: "स्वर्ण",
            1: "रजत",
            2: "ताम्र",
            3: "लोह"
        }

        paya = paya_map.get(
            moon_rashi % 4,
            "रजत"
        )

        return jsonify({

            "success": True,

            "birth_details":
                birth_details,

            "lagna": {
                "rashi":
                    RASHI_NAMES[
                        asc_rashi
                    ],

                "rashi_num":
                    asc_rashi + 1,

                "degree":
                    degree_text(
                        asc_lon
                    ),

                "longitude":
                    round(
                        asc_lon,
                        6
                    )
            },

            "basic": {
                "rashi":
                    RASHI_NAMES[
                        moon_rashi
                    ],

                "rashi_lord":
                    RASHI_LORDS[
                        moon_rashi
                    ],

                "janma_nakshatra":
                    nak_name,

                "nakshatra_pada":
                    nak_pada,

                "nakshatra_lord":
                    nak_lord,

                "paya":
                    paya,

                "yoni":
                    YONI[
                        nak_idx
                    ],

                "gana":
                    GANA[
                        nak_idx
                    ],

                "nadi":
                    NADI[
                        nak_idx
                    ],

                "varna":
                    VARNA_BY_RASHI[
                        moon_rashi
                    ],

                "manglik":
                    manglik
            },

            "panchang":
                panchang,

            "planets":
                planet_data,

            "houses":
                houses,

            "chart": {
                "type":
                    "north_indian",

                "style":
                    "whole_sign",

                "ascendant_house":
                    1,

                "houses":
                    houses
            },

            "dasha":
                dasha
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# DASHA
# ============================================================

@app.get(
    "/api/dasha"
)
def dasha_api():

    try:

        date_str = (
            request.args.get(
                "date"
            )
            or request.args.get(
                "dob"
            )
        )

        time_str = request.args.get(
            "time"
        )

        birth_dt = parse_date_time(
            date_str,
            time_str
        )

        jd = get_julian_day(
            birth_dt
        )

        moon_lon, _ = (
            sidereal_position(
                jd,
                swe.MOON
            )
        )

        return jsonify({
            "success": True,
            "data":
                calculate_vimshottari(
                    birth_dt,
                    moon_lon
                )
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# LOCATION
# ============================================================

@app.get(
    "/api/location"
)
def location_api():

    try:

        q = request.args.get(
            "q",
            ""
        ).strip()

        if len(q) < 2:
            return jsonify({
                "success": False,
                "error":
                    "Enter city or pincode"
            }), 400

        return jsonify({
            "success": True,
            "results":
                location_search(q)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# MUHURT CATEGORY LIST
# ============================================================

@app.get(
    "/api/muhurt-types"
)
def muhurt_types_api():

    result = []

    for key, value in (
        MUHURT_TYPES.items()
    ):

        result.append({
            "id": key,
            "name": value[
                "name"
            ],

            "birth_required":
                value.get(
                    "birth_required",
                    False
                ),

            "extra_fields":
                value.get(
                    "extra",
                    []
                )
        })

    return jsonify({
        "success": True,
        "count": len(result),
        "categories": result
    })


# ============================================================
# MUHURT SEARCH
# ============================================================

@app.route(
    "/api/muhurt",
    methods=["GET", "POST"]
)
def muhurt_api():

    try:

        if request.method == "POST":

            payload = (
                request.get_json(
                    silent=True
                )
                or {}
            )

        else:

            payload = dict(
                request.args
            )

        result = search_muhurt(
            payload
        )

        return jsonify(
            result
        )

    except ValueError as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
