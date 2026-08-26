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

# ============================================================
# RASHI
# ============================================================

RASHI_NAMES = [
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
]

RASHI_LORDS = [
    "मंगल", "शुक्र", "बुध", "चंद्र", "सूर्य", "बुध",
    "शुक्र", "मंगल", "गुरु", "शनि", "शनि", "गुरु"
]

# ============================================================
# NAKSHATRA
# ============================================================

NAKSHATRA_NAMES = [
    "अश्विनी",
    "भरणी",
    "कृत्तिका",
    "रोहिणी",
    "मृगशिरा",
    "आर्द्रा",
    "पुनर्वसु",
    "पुष्य",
    "आश्लेषा",
    "मघा",
    "पूर्वा फाल्गुनी",
    "उत्तरा फाल्गुनी",
    "हस्त",
    "चित्रा",
    "स्वाती",
    "विशाखा",
    "अनुराधा",
    "ज्येष्ठा",
    "मूल",
    "पूर्वाषाढ़ा",
    "उत्तराषाढ़ा",
    "श्रवण",
    "धनिष्ठा",
    "शतभिषा",
    "पूर्वा भाद्रपद",
    "उत्तरा भाद्रपद",
    "रेवती"
]

NAKSHATRA_LORDS = [
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु",
    "गुरु", "शनि", "बुध", "केतु", "शुक्र", "सूर्य",
    "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु",
    "गुरु", "शनि", "बुध"
]

# ============================================================
# NAKSHATRA PADA NAMAKSHARA
# ============================================================

NAMAKSHARA = [
    ["चू", "चे", "चो", "ला"],
    ["ली", "लू", "ले", "लो"],
    ["अ", "ई", "उ", "ए"],
    ["ओ", "वा", "वी", "वू"],
    ["वे", "वो", "का", "की"],
    ["कू", "घ", "ङ", "छ"],
    ["के", "को", "हा", "ही"],
    ["हू", "हे", "हो", "डा"],
    ["डी", "डू", "डे", "डो"],
    ["मा", "मी", "मू", "मे"],
    ["मो", "टा", "टी", "टू"],
    ["टे", "टो", "पा", "पी"],
    ["पू", "ष", "ण", "ठ"],
    ["पे", "पो", "रा", "री"],
    ["रू", "रे", "रो", "ता"],
    ["ती", "तू", "ते", "तो"],
    ["ना", "नी", "नू", "ने"],
    ["नो", "या", "यी", "यू"],
    ["ये", "यो", "भा", "भी"],
    ["भू", "धा", "फा", "ढा"],
    ["भे", "भो", "जा", "जी"],
    ["खी", "खू", "खे", "खो"],
    ["गा", "गी", "गू", "गे"],
    ["गो", "सा", "सी", "सू"],
    ["से", "सो", "दा", "दी"],
    ["दू", "थ", "झ", "ञ"],
    ["दे", "दो", "चा", "ची"]
]

# ============================================================
# TITHI
# ============================================================

TITHI_NAMES = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

# ============================================================
# YOGA
# ============================================================

YOGA_NAMES = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन",
    "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि",
    "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात",
    "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ",
    "शुक्ल", "ब्रह्म", "ऐन्द्र", "वैधृति"
]

# ============================================================
# KARANA
# ============================================================

KARANA_FIXED = {
    0: "किंस्तुघ्न",
    57: "शकुनि",
    58: "चतुष्पाद",
    59: "नाग"
}

KARANA_MOVING = [
    "बव", "बालव", "कौलव", "तैतिल",
    "गर", "वणिज", "विष्टि"
]

# ============================================================
# WEEKDAYS
# ============================================================

WEEKDAYS = [
    "सोमवार", "मंगलवार", "बुधवार",
    "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"
]

# ============================================================
# MONTHS
# ============================================================

HINDI_MONTHS = [
    "चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़",
    "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक",
    "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"
]

PLANET_ORDER = [
    "सूर्य", "चंद्र", "मंगल", "बुध",
    "गुरु", "शुक्र", "शनि", "राहु", "केतु"
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

YONI = [
    "अश्व", "गज", "मेष", "सर्प", "सर्प", "श्वान",
    "मार्जार", "मेष", "मार्जार", "मूषक", "मूषक",
    "गौ", "महिष", "व्याघ्र", "महिष", "व्याघ्र",
    "मृग", "मृग", "श्वान", "वानर", "नकुल",
    "वानर", "अश्व", "गज", "अश्व", "सिंह", "गौ"
]

GANA = [
    "देव", "मनुष्य", "राक्षस", "मनुष्य", "देव",
    "मनुष्य", "देव", "देव", "राक्षस", "राक्षस",
    "मनुष्य", "मनुष्य", "देव", "राक्षस", "देव",
    "राक्षस", "देव", "राक्षस", "राक्षस", "मनुष्य",
    "मनुष्य", "देव", "राक्षस", "राक्षस", "मनुष्य",
    "मनुष्य", "देव"
]

NADI = [
    "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य",
    "आदि", "आदि", "मध्य", "अन्त्य", "अन्त्य",
    "मध्य", "आदि", "आदि", "मध्य", "अन्त्य",
    "अन्त्य", "मध्य", "आदि", "आदि", "मध्य",
    "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि",
    "मध्य", "अन्त्य"
]

VARNA_BY_RASHI = {
    0: "क्षत्रिय",
    1: "वैश्य",
    2: "शूद्र",
    3: "ब्राह्मण",
    4: "क्षत्रिय",
    5: "वैश्य",
    6: "शूद्र",
    7: "ब्राह्मण",
    8: "क्षत्रिय",
    9: "वैश्य",
    10: "शूद्र",
    11: "ब्राह्मण"
}

# ============================================================
# BASIC HELPERS
# ============================================================

def get_julian_day(local_dt):
    utc_dt = local_dt.astimezone(pytz.utc)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour +
        utc_dt.minute / 60.0 +
        utc_dt.second / 3600.0
    )


def normalize(deg):
    return deg % 360.0


def parse_date_time(date_str, time_str):
    if not date_str:
        raise ValueError("Date is required")

    if not time_str:
        raise ValueError("Time is required")

    y, m, d = map(int, date_str.split("-"))

    parts = time_str.split(":")
    hh = int(parts[0])
    mm = int(parts[1]) if len(parts) > 1 else 0
    ss = int(parts[2]) if len(parts) > 2 else 0

    return IST.localize(
        dt.datetime(y, m, d, hh, mm, ss)
    )


def degree_text(lon):
    local = lon % 30.0
    deg = int(local)

    minute_float = (local - deg) * 60.0
    minute = int(minute_float)

    second = int(
        round(
            (minute_float - minute) * 60
        )
    )

    if second == 60:
        second = 0
        minute += 1

    if minute >= 60:
        minute = 0
        deg += 1

    return f'{deg}°{minute:02d}\'{second:02d}"'


def rashi_index(lon):
    return int(normalize(lon) / 30.0) % 12


def nakshatra_info(lon):
    span = 360.0 / 27.0
    normalized_lon = normalize(lon)

    idx = min(
        26,
        int(normalized_lon / span)
    )

    within = normalized_lon - (idx * span)

    pada = min(
        4,
        int(within / (span / 4.0)) + 1
    )

    nak_name = NAKSHATRA_NAMES[idx]
    nak_lord = NAKSHATRA_LORDS[idx]
    namakshara = NAMAKSHARA[idx][pada - 1]

    return (
        idx,
        nak_name,
        pada,
        nak_lord,
        namakshara
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


# ============================================================
# PURNIMANTA MONTH
# ============================================================

def calculate_purnimanta_month(sun_lon, moon_lon):
    sun_rashi = int(sun_lon / 30.0) % 12
    angle_diff = normalize(moon_lon - sun_lon)
    tithi_deg = angle_diff / 12.0
    base_idx = sun_rashi

    if tithi_deg >= 15:
        purnimant_idx = (base_idx + 1) % 12
    else:
        purnimant_idx = base_idx

    return HINDI_MONTHS[purnimant_idx]


# ============================================================
# PANCHANG
# ============================================================

def karana_name(index):
    if index in KARANA_FIXED:
        return KARANA_FIXED[index]

    if 1 <= index <= 56:
        return KARANA_MOVING[(index - 1) % 7]

    return "--"


def find_sun_event(y, m, d, lat, lon, rising=True):
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
            value_dt = pytz.utc.localize(value_dt)

        return value_dt.astimezone(IST)

    except Exception:
        return None


def moon_event(y, m, d, lat, lon, rising=True):
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
            value_dt = pytz.utc.localize(value_dt)

        return value_dt.astimezone(IST)

    except Exception:
        return None


def event_time_text(value, base_date):
    if not value:
        return "--"

    suffix = (
        "अगले दिन "
        if value.date() > base_date
        else ""
    )

    return suffix + value.strftime("%I:%M %p")


# ============================================================
# ALL 8 MUHURTAS CALCULATION (Matching Frontend Keys)
# ============================================================

def calculate_all_muhurtas(sunrise_dt, sunset_dt):
    if not sunrise_dt or not sunset_dt:
        return {
            "abhijit_muhurta": "—",
            "rahu_kal": "—",
            "gulika_kal": "—",
            "durmuhurt": "—",
            "varjyam": "—",
            "brahma_muhurta": "—",
            "yamagand": "—",
            "pradosh": "—"
        }

    weekday = sunrise_dt.weekday() # 0:Mon, 1:Tue, 2:Wed, 3:Thu, 4:Fri, 5:Sat, 6:Sun
    day_duration = (sunset_dt - sunrise_dt).total_seconds()
    day_part = day_duration / 8.0
    day_muhurta_len = day_duration / 15.0

    # 1. Abhijit Muhurta (approx middle of day, ~48 mins)
    abhijeet_start = sunrise_dt + dt.timedelta(seconds=6 * day_muhurta_len)
    abhijeet_end = abhijeet_start + dt.timedelta(minutes=48)
    abhijeet_str = f"{abhijeet_start.strftime('%I:%M %p')} - {abhijeet_end.strftime('%I:%M %p')}"

    # 2. Rahu Kal
    rahu_parts = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
    r_part = rahu_parts.get(weekday, 2)
    rk_start = sunrise_dt + dt.timedelta(seconds=(r_part - 1) * day_part)
    rk_end = rk_start + dt.timedelta(seconds=day_part)
    rahu_str = f"{rk_start.strftime('%I:%M %p')} - {rk_end.strftime('%I:%M %p')}"

    # 3. Gulika Kal
    gulika_parts = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
    g_part = gulika_parts.get(weekday, 6)
    gk_start = sunrise_dt + dt.timedelta(seconds=(g_part - 1) * day_part)
    gk_end = gk_start + dt.timedelta(seconds=day_part)
    gulika_str = f"{gk_start.strftime('%I:%M %p')} - {gk_end.strftime('%I:%M %p')}"

    # 4. Durmuhurt
    durmuhurt_parts = {
        0: [8],
        1: [1, 7],
        2: [5],
        3: [4, 6],
        4: [2],
        5: [3],
        6: [4]
    }
    dm_list = durmuhurt_parts.get(weekday, [8])
    dm_starts = [sunrise_dt + dt.timedelta(seconds=(p - 1) * day_muhurta_len) for p in dm_list]
    dm_ends = [s + dt.timedelta(seconds=day_muhurta_len) for s in dm_starts]
    dur_str = ", ".join([f"{s.strftime('%I:%M %p')} - {e.strftime('%I:%M %p')}" for s, e in zip(dm_starts, dm_ends)])

    # 5. Varjyam
    varjyam_start = sunrise_dt + dt.timedelta(seconds=day_duration * 0.6)
    varjyam_end = varjyam_start + dt.timedelta(minutes=96)
    varjyam_str = f"{varjyam_start.strftime('%I:%M %p')} - {varjyam_end.strftime('%I:%M %p')}"

    # 6. Brahma Muhurta
    bm_start = sunrise_dt - dt.timedelta(minutes=96)
    bm_end = sunrise_dt - dt.timedelta(minutes=48)
    brahma_str = f"{bm_start.strftime('%I:%M %p')} - {bm_end.strftime('%I:%M %p')}"

    # 7. Yamagand
    yamagand_part_map = {6: 4, 0: 5, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6}
    yg_part = yamagand_part_map.get(weekday, 5)
    yg_start = sunrise_dt + dt.timedelta(seconds=(yg_part - 1) * day_muhurta_len)
    yg_end = yg_start + dt.timedelta(seconds=day_muhurta_len)
    yamgand_str = f"{yg_start.strftime('%I:%M %p')} - {yg_end.strftime('%I:%M %p')}"

    # 8. Pradosh Kal
    pradosha_start = sunset_dt
    pradosha_end = sunset_dt + dt.timedelta(minutes=120)
    pradosha_str = f"{pradosha_start.strftime('%I:%M %p')} - {pradosha_end.strftime('%I:%M %p')}"

    return {
        "abhijit_muhurta": abhijeet_str,
        "rahu_kal": rahu_str,
        "gulika_kal": gulika_str,
        "durmuhurt": dur_str,
        "varjyam": varjyam_str,
        "brahma_muhurta": brahma_str,
        "yamagand": yamgand_str,
        "pradosh": pradosha_str
    }


def panchang_for_date(date_str, city, lat, lon):
    y, m, d = map(int, date_str.split("-"))

    local_dt = IST.localize(
        dt.datetime(y, m, d, 12, 0)
    )

    jd = get_julian_day(
        local_dt
    )

    swe.set_sid_mode(
        swe.SIDM_LAHIRI
    )

    sun_lon, sun_speed = sidereal_position(
        jd,
        swe.SUN
    )

    moon_lon, moon_speed = sidereal_position(
        jd,
        swe.MOON
    )

    angle_diff = normalize(
        moon_lon - sun_lon
    )

    tithi_position = (
        angle_diff / 12.0
    )

    tithi_idx = min(
        29,
        int(tithi_position)
    )

    paksha = (
        "शुक्ल पक्ष"
        if tithi_idx < 15
        else "कृष्ण पक्ष"
    )

    rel_speed = (
        moon_speed - sun_speed
    )

    tithi_end = None

    if rel_speed > 0:
        degrees_left = (
            ((tithi_idx + 1) * 12.0)
            - angle_diff
        )

        end_jd = (
            jd +
            degrees_left / rel_speed
        )

        y2, m2, d2, h2 = swe.revjul(
            end_jd,
            swe.GREG_CAL
        )

        utc_end = pytz.utc.localize(
            dt.datetime(
                y2,
                m2,
                d2
            )
            +
            dt.timedelta(
                hours=h2
            )
        )

        tithi_end = utc_end.astimezone(
            IST
        )

    (
        nak_idx,
        nak_name,
        nak_pada,
        nak_lord,
        namakshara
    ) = nakshatra_info(
        moon_lon
    )

    yoga_idx = int(
        normalize(
            sun_lon + moon_lon
        )
        /
        (360.0 / 27.0)
    )

    yoga_idx = min(
        26,
        yoga_idx
    )

    karana_position = (
        angle_diff / 6.0
    )

    karana_idx = int(
        karana_position
    )

    karan_1 = karana_name(
        karana_idx
    )

    karan_2 = karana_name(
        (karana_idx + 1) % 60
    )

    sun_rashi_idx = rashi_index(
        sun_lon
    )

    moon_rashi_idx = rashi_index(
        moon_lon
    )

    vikram = y + 57
    shaka = y - 78
    kali = y + 3101

    sunrise_dt = find_sun_event(
        y, m, d,
        lat, lon,
        True
    )

    sunset_dt = find_sun_event(
        y, m, d,
        lat, lon,
        False
    )

    moonrise_dt = moon_event(
        y, m, d,
        lat, lon,
        True
    )

    moonset_dt = moon_event(
        y, m, d,
        lat, lon,
        False
    )

    # Calculate all 8 Muhurtas for frontend keys
    muhurtas = calculate_all_muhurtas(sunrise_dt, sunset_dt)

    ayan = (
        "उत्तरायण"
        if sun_rashi_idx in [
            9, 10, 11,
            0, 1, 2
        ]
        else "दक्षिणायन"
    )

    ritu_map = {
        11: "वसंत",
        0: "वसंत",
        1: "ग्रीष्म",
        2: "ग्रीष्म",
        3: "वर्षा",
        4: "वर्षा",
        5: "शरद",
        6: "शरद",
        7: "हेमंत",
        8: "हेमंत",
        9: "शिशिर",
        10: "शिशिर"
    }

    ishta_kaal = "--"

    if sunrise_dt:
        noon_dt = IST.localize(
            dt.datetime(
                y, m, d, 12, 0
            )
        )

        minutes = max(
            0,
            int(
                (
                    noon_dt -
                    sunrise_dt
                ).total_seconds()
                / 60
            )
        )

        ghati = minutes // 24

        pala = int(
            (minutes % 24) * 2.5
        )

        ishta_kaal = (
            f"{ghati} घटी "
            f"{pala} पल"
        )

    maah_purnimant = (
        calculate_purnimanta_month(
            sun_lon,
            moon_lon
        )
    )

    return {
        "success": True,
        "data": {
            "location": {
                "city": city,
                "latitude": lat,
                "longitude": lon
            },
            "summary_header":
                f"{TITHI_NAMES[tithi_idx]}, "
                f"{nak_name} नक्षत्र",

            "details": {
                "tithi":
                    TITHI_NAMES[
                        tithi_idx
                    ],

                "tithi_end_time":
                    event_time_text(
                        tithi_end,
                        local_dt.date()
                    ),

                "paksha": paksha,
                "nakshatra": nak_name,
                "nakshatra_pada": nak_pada,
                "nakshatra_lord": nak_lord,
                "namakshara": namakshara,

                "yog":
                    YOGA_NAMES[
                        yoga_idx
                    ],

                "karan_1": karan_1,
                "karan_2": karan_2,

                "var":
                    WEEKDAYS[
                        local_dt.weekday()
                    ],

                "chandra_rashi":
                    RASHI_NAMES[
                        moon_rashi_idx
                    ],

                "surya_rashi":
                    RASHI_NAMES[
                        sun_rashi_idx
                    ],

                "vikram_samvat":
                    str(vikram),

                "shaka_samvat":
                    str(shaka),

                "kali_samvat":
                    str(kali),

                "ayan": ayan,

                "ritu":
                    ritu_map.get(
                        sun_rashi_idx,
                        "--"
                    ),

                "maah_purnimant":
                    maah_purnimant,

                "ishta_kaal":
                    ishta_kaal
            },

            # Added under special_timings so JS findValue() can easily capture all 8 muhurtas
            "special_timings": {
                "abhijit_muhurta": muhurtas["abhijit_muhurta"],
                "rahu_kal": muhurtas["rahu_kal"],
                "gulika_kal": muhurtas["gulika_kal"],
                "durmuhurt": muhurtas["durmuhurt"],
                "varjyam": muhurtas["varjyam"],
                "brahma_muhurta": muhurtas["brahma_muhurta"],
                "yamagand": muhurtas["yamagand"],
                "pradosh": muhurtas["pradosh"]
            },

            "timings": {
                "sunrise":
                    sunrise_dt.strftime(
                        "%I:%M %p"
                    )
                    if sunrise_dt
                    else "--",

                "sunset":
                    sunset_dt.strftime(
                        "%I:%M %p"
                    )
                    if sunset_dt
                    else "--",

                "chandrodaya":
                    moonrise_dt.strftime(
                        "%I:%M %p"
                    )
                    if moonrise_dt
                    else "--",

                "chandrast":
                    moonset_dt.strftime(
                        "%I:%M %p"
                    )
                    if moonset_dt
                    else "--"
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
    sign_idx = rashi_index(lon)

    nak_idx, nak_name, nak_pada, nak_lord, namakshara = (
        nakshatra_info(lon)
    )

    degree = lon % 30.0

    sun_distance = abs(
        normalize(lon - sun_lon)
    )

    if sun_distance > 180:
        sun_distance = (
            360 - sun_distance
        )

    combustion_limits = {
        "चंद्र": 12,
        "मंगल": 17,
        "बुध": 14,
        "गुरु": 11,
        "शुक्र": 10,
        "शनि": 15
    }

    is_asta = False

    if (
        name in combustion_limits
        and sun_distance <=
        combustion_limits[name]
    ):
        is_asta = True

    return {
        "name": name,
        "longitude": round(lon, 6),
        "rashi":
            RASHI_NAMES[
                sign_idx
            ],
        "rashi_num":
            sign_idx + 1,
        "degree":
            degree_text(lon),
        "nakshatra": nak_name,
        "nakshatra_pada": nak_pada,
        "nakshatra_lord": nak_lord,
        "namakshara": namakshara,
        "speed": round(speed, 6),
        "is_vakri": speed < 0,
        "motion":
            "वक्री"
            if speed < 0
            else "मार्गी",
        "is_asta": is_asta
    }


def calculate_houses(
    jd,
    lat,
    lon
):
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
            normalize(c - ayan)
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
            -
            rashi_index(asc_lon)
        )
        % 12
    ) + 1


def manglik_status(
    mars_rashi,
    asc_rashi
):
    house = (
        (
            mars_rashi -
            asc_rashi
        )
        % 12
    ) + 1

    is_manglik = house in [
        1, 4, 7, 8, 12
    ]

    return {
        "is_manglik": is_manglik,
        "status":
            "मांगलिक है"
            if is_manglik
            else "मांगलिक नहीं",
        "mars_house_from_lagna":
            house
    }


# ============================================================
# VIMSHOTTARI DASHA
# ============================================================

def add_years(
    base_date,
    years
):
    days = years * 365.2425

    return (
        base_date +
        dt.timedelta(
            days=days
        )
    )


def dasha_sequence(
    start_lord
):
    idx = DASHA_ORDER.index(
        start_lord
    )

    return (
        DASHA_ORDER[idx:]
        +
        DASHA_ORDER[:idx]
    )


def build_antardashas(
    maha_lord,
    maha_start,
    maha_end,
    now
):
    total_maha_days = (
        maha_end -
        maha_start
    ).total_seconds() / 86400.0

    result = []

    cursor = maha_start

    for lord in dasha_sequence(
        maha_lord
    ):
        duration_days = (
            total_maha_days
            *
            DASHA_YEARS[lord]
            /
            120.0
        )

        end = (
            cursor +
            dt.timedelta(
                days=duration_days
            )
        )

        result.append({
            "planet": lord,
            "start":
                cursor.strftime(
                    "%d-%m-%Y"
                ),
            "end":
                end.strftime(
                    "%d-%m-%Y"
                ),
            "current":
                cursor <= now < end
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
        nak_lord,
        namakshara
    ) = nakshatra_info(
        moon_lon
    )

    span = 360.0 / 27.0

    nak_start = nak_idx * span

    travelled = (
        normalize(moon_lon)
        -
        nak_start
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
        *
        (
            1.0 -
            fraction_completed
        )
    )

    birth_date = dob_local
    cursor = birth_date

    now = dt.datetime.now(
        IST
    )

    mahadashas = []

    first = True

    while len(mahadashas) < 18:
        lord = (
            first_lord
            if first
            else DASHA_ORDER[
                (
                    DASHA_ORDER.index(
                        first_lord
                    )
                    +
                    len(mahadashas)
                )
                % 9
            ]
        )

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

            "start":
                cursor.strftime(
                    "%d-%m-%Y"
                ),

            "end":
                end.strftime(
                    "%d-%m-%Y"
                ),

            "years":
                round(
                    years,
                    4
                ),

            "current":
                cursor <= now < end,

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
            x for x in mahadashas
            if x["current"]
        ),
        None
    )

    return {
        "nakshatra": nak_name,
        "nakshatra_pada": pada,
        "namakshara": namakshara,
        "starting_mahadasha":
            first_lord,

        "current_mahadasha":
            current_maha["planet"]
            if current_maha
            else None,

        "mahadasha":
            mahadashas
    }


# ============================================================
# LOCATION SEARCH
# ============================================================

POSTAL_API = (
    "https://api.postalpincode.in"
)

NOMINATIM_API = (
    "https://nominatim.openstreetmap.org/search"
)

USER_AGENT = (
    "HindiPanchang-Kundali/2.1"
)


def http_json(
    url,
    timeout=12
):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                USER_AGENT,

            "Accept":
                "application/json"
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=timeout
    ) as response:
        return json.loads(
            response.read()
            .decode("utf-8")
        )


def geocode_india(
    query,
    limit=8
):
    params = urllib.parse.urlencode({
        "q":
            query + ", India",

        "format":
            "jsonv2",

        "addressdetails":
            1,

        "limit":
            limit,

        "countrycodes":
            "in"
    })

    items = http_json(
        NOMINATIM_API +
        "?" +
        params
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
                    query
                ),

            "city":
                (
                    address.get("city")
                    or
                    address.get("town")
                    or
                    address.get("village")
                    or
                    address.get("municipality")
                    or
                    address.get("county")
                    or
                    query
                ),

            "district":
                (
                    address.get(
                        "state_district"
                    )
                    or
                    address.get("district")
                    or
                    address.get("county")
                    or
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
                    "India"
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


def postal_lookup(
    query
):
    q = (
        query or ""
    ).strip()

    if not q:
        return []

    if re.fullmatch(
        r"\d{6}",
        q
    ):
        url = (
            f"{POSTAL_API}/pincode/{q}"
        )
    else:
        url = (
            f"{POSTAL_API}/postoffice/"
            f"{urllib.parse.quote(q)}"
        )

    try:
        payload = http_json(
            url
        )

    except Exception:
        return []

    if (
        not isinstance(
            payload,
            list
        )
        or
        not payload
    ):
        return []

    first = payload[0] or {}

    if (
        str(
            first.get(
                "Status",
                ""
            )
        ).lower()
        !=
        "success"
    ):
        return []

    offices = (
        first.get(
            "PostOffice"
        )
        or
        []
    )

    result = []

    for office in offices:
        result.append({
            "post_office":
                office.get(
                    "Name",
                    ""
                ),

            "branch_type":
                office.get(
                    "BranchType",
                    ""
                ),

            "delivery_status":
                office.get(
                    "DeliveryStatus",
                    ""
                ),

            "division":
                office.get(
                    "Division",
                    ""
                ),

            "region":
                office.get(
                    "Region",
                    ""
                ),

            "circle":
                office.get(
                    "Circle",
                    ""
                ),

            "district":
                office.get(
                    "District",
                    ""
                ),

            "state":
                office.get(
                    "State",
                    ""
                ),

            "pincode":
                office.get(
                    "Pincode",
                    ""
                )
        })

    return result


def location_search(
    query
):
    q = (
        query or ""
    ).strip()

    if len(q) < 2:
        return []

    postal = postal_lookup(q)

    results = []

    for office in postal[:12]:
        geo_query = ", ".join(
            x for x in [
                office["post_office"],
                office["district"],
                office["state"],
                office["pincode"]
            ]
            if x
        )

        try:
            geo = geocode_india(
                geo_query,
                limit=1
            )

        except Exception:
            geo = []

        if not geo:
            try:
                geo = geocode_india(
                    ", ".join(
                        x for x in [
                            office["district"],
                            office["state"]
                        ]
                        if x
                    ),
                    limit=1
                )

            except Exception:
                geo = []

        if not geo:
            continue

        g = geo[0]

        results.append({
            "display_name":
                f'{office["post_office"]}, '
                f'{office["district"]}, '
                f'{office["state"]} - '
                f'{office["pincode"]}',

            "city":
                office[
                    "post_office"
                ],

            "district":
                office[
                    "district"
                ],

            "state":
                office[
                    "state"
                ],

            "pincode":
                office[
                    "pincode"
                ],

            "country":
                "India",

            "post_office":
                office[
                    "post_office"
                ],

            "branch_type":
                office[
                    "branch_type"
                ],

            "delivery_status":
                office[
                    "delivery_status"
                ],

            "latitude":
                g["latitude"],

            "longitude":
                g["longitude"]
        })

    if results:
        seen = set()
        unique = []

        for item in results:
            key = (
                item["post_office"],
                item["pincode"],
                item["latitude"],
                item["longitude"]
            )

            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique[:12]

    try:
        return geocode_india(
            q,
            limit=8
        )

    except Exception:
        return []


def parse_location(
    source
):
    city = (
        source.get(
            "city"
        )
        or
        ""
    ).strip()

    lat_raw = source.get(
        "lat"
    )

    lon_raw = source.get(
        "lon"
    )

    if (
        lat_raw not in (
            None,
            ""
        )
        and
        lon_raw not in (
            None,
            ""
        )
    ):
        try:
            return (
                city or DEFAULT_CITY,
                float(lat_raw),
                float(lon_raw)
            )

        except (
            TypeError,
            ValueError
        ):
            raise ValueError(
                "Invalid latitude/longitude"
            )

    if city:
        matches = location_search(
            city
        )

        if matches:
            x = matches[0]

            return (
                x["display_name"],
                x["latitude"],
                x["longitude"]
            )

        raise ValueError(
            "Location not found. "
            "Select a valid Indian "
            "PIN/Post Office/City."
        )

    return (
        DEFAULT_CITY,
        DEFAULT_LAT,
        DEFAULT_LON
    )


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    return jsonify({
        "success": True,
        "service":
            "Hindi Panchang &amp; Kundali API",
        "status":
            "online",
        "version":
            "2.2"
    })


@app.get("/health")
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })


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
# LIVE ALL-PLANET TRANSITS
# ============================================================

def normalize_transit_planet_name(
    planet_name
):
    aliases = {
        "चन्द्र": "चंद्र",
        "Chandra": "चंद्र",
        "Moon": "चंद्र",
        "moon": "चंद्र",

        "Surya": "सूर्य",
        "Sun": "सूर्य",
        "sun": "सूर्य",

        "Mangal": "मंगल",
        "Mars": "मंगल",
        "mars": "मंगल",

        "Budh": "बुध",
        "Mercury": "बुध",
        "mercury": "बुध",

        "Guru": "गुरु",
        "Jupiter": "गुरु",
        "jupiter": "गुरु",

        "Shukra": "शुक्र",
        "Venus": "शुक्र",
        "venus": "शुक्र",

        "Shani": "शनि",
        "Saturn": "शनि",
        "saturn": "शनि",

        "Rahu": "राहु",
        "rahu": "राहु",

        "Ketu": "केतु",
        "ketu": "केतु"
    }

    return aliases.get(
        planet_name,
        planet_name
    )


def _utc_jd(
    moment
):
    if moment.tzinfo is None:
        moment = pytz.utc.localize(
            moment
        )

    moment = moment.astimezone(
        pytz.utc
    )

    return swe.julday(
        moment.year,
        moment.month,
        moment.day,

        moment.hour
        +
        moment.minute / 60.0
        +
        (
            moment.second
            +
            moment.microsecond / 1000000.0
        )
        / 3600.0
    )


def _transit_position(
    jd,
    planet_name
):
    swe.set_sid_mode(
        swe.SIDM_LAHIRI
    )

    planet_name = (
        normalize_transit_planet_name(
            planet_name
        )
    )

    if planet_name == "केतु":
        rahu_lon, _ = sidereal_position(
            jd,
            swe.MEAN_NODE
        )

        return (
            normalize(
                rahu_lon + 180.0
            ),
            -1.0
        )

    if planet_name not in PLANET_IDS:
        raise ValueError(
            f"Unknown planet: "
            f"{planet_name}"
        )

    return sidereal_position(
        jd,
        PLANET_IDS[
            planet_name
        ]
    )


def _transit_state(
    moment,
    planet_name
):
    lon, speed = _transit_position(
        _utc_jd(moment),
        planet_name
    )

    return (
        rashi_index(lon),
        lon,
        speed
    )


def _refine_transit(
    start,
    end,
    planet_name,
    old_sign
):
    for _ in range(30):
        mid = (
            start
            +
            (
                end - start
            )
            / 2
        )

        sign, _, _ = _transit_state(
            mid,
            planet_name
        )

        if sign == old_sign:
            start = mid
        else:
            end = mid

    return end


def _collect_transits_for_planet(
    start,
    end,
    planet_name,
    step_hours=24
):
    planet_name = (
        normalize_transit_planet_name(
            planet_name
        )
    )

    events = []

    cursor = start

    old_sign, _, _ = _transit_state(
        cursor,
        planet_name
    )

    while cursor < end:
        nxt = min(
            cursor +
            dt.timedelta(
                hours=step_hours
            ),
            end
        )

        new_sign, _, _ = _transit_state(
            nxt,
            planet_name
        )

        if new_sign != old_sign:
            when = _refine_transit(
                cursor,
                nxt,
                planet_name,
                old_sign
            )

            after_sign, _, after_speed = (
                _transit_state(
                    when +
                    dt.timedelta(
                        seconds=2
                    ),
                    planet_name
                )
            )

            local_when = (
                when.astimezone(
                    IST
                )
            )

            events.append({
                "planet":
                    planet_name,

                "from_rashi":
                    RASHI_NAMES[
                        old_sign
                    ],

                "to_rashi":
                    RASHI_NAMES[
                        after_sign
                    ],

                "date":
                    local_when.isoformat(),

                "transit_date":
                    local_when.strftime(
                        "%Y-%m-%d"
                    ),

                "transit_time":
                    local_when.strftime(
                        "%H:%M:%S"
                    ),

                "motion":
                    (
                        "वक्री"
                        if after_speed < 0
                        else "मार्गी"
                    ),

                "timestamp":
                    when.timestamp()
            })

            old_sign = after_sign

            cursor = (
                when +
                dt.timedelta(
                    seconds=5
                )
            )

        else:
            cursor = nxt

    events.sort(
        key=lambda x:
            x["timestamp"]
    )

    return events


def _collect_transits(
    start,
    end,
    step_hours=2
):
    events = []

    for planet_name in PLANET_ORDER:
        events.extend(
            _collect_transits_for_planet(
                start,
                end,
                planet_name,
                step_hours=step_hours
            )
        )

    events.sort(
        key=lambda x:
            x["timestamp"]
    )

    return events


def _current_transit_positions(
    now
):
    rows = []

    for planet_name in PLANET_ORDER:
        sign_idx, lon, speed = (
            _transit_state(
                now,
                planet_name
            )
        )

        sign_degree = lon % 30.0

        degree = int(
            sign_degree
        )

        minute = int(
            (
                sign_degree -
                degree
            )
            * 60
        )

        (
            nak_idx,
            nak_name,
            nak_pada,
            _,
            _
        ) = nakshatra_info(
            lon
        )

        rows.append({
            "planet":
                planet_name,

            "rashi":
                RASHI_NAMES[
                    sign_idx
                ],

            "degree":
                f"{degree}° {minute:02d}'",

            "nakshatra":
                nak_name,

            "pada":
                nak_pada,

            "motion":
                (
                    "वक्री"
                    if speed < 0
                    else "मार्गी"
                )
        })

    return rows


_TRANSIT_SEARCH = {
    "सूर्य": {
        "days": 180,
        "step_hours": 12
    },

    "चंद्र": {
        "days": 20,
        "step_hours": 2
    },

    "मंगल": {
        "days": 1200,
        "step_hours": 24
    },

    "बुध": {
        "days": 240,
        "step_hours": 12
    },

    "गुरु": {
        "days": 4500,
        "step_hours": 72
    },

    "शुक्र": {
        "days": 500,
        "step_hours": 12
    },

    "शनि": {
        "days": 15000,
        "step_hours": 168
    },

    "राहु": {
        "days": 3000,
        "step_hours": 72
    },

    "केतु": {
        "days": 3000,
        "step_hours": 72
    }
}


def _three_transits_each_side(
    now,
    planet_name
):
    planet_name = (
        normalize_transit_planet_name(
            planet_name
        )
    )

    cfg = _TRANSIT_SEARCH[
        planet_name
    ]

    days = cfg["days"]

    step_hours = (
        cfg["step_hours"]
    )

    past_events = (
        _collect_transits_for_planet(
            now -
            dt.timedelta(
                days=days
            ),
            now,
            planet_name,
            step_hours=step_hours
        )
    )

    future_events = (
        _collect_transits_for_planet(
            now,
            now +
            dt.timedelta(
                days=days
            ),
            planet_name,
            step_hours=step_hours
        )
    )

    return {
        "past":
            list(
                reversed(
                    past_events[-3:]
                )
            ),

        "future":
            future_events[:3]
    }


@app.get("/api/all-transits")
def all_transits():
    try:
        now = dt.datetime.now(
            pytz.utc
        )

        current_rows = (
            _current_transit_positions(
                now
            )
        )

        current_by_planet = {
            row["planet"]: row
            for row in current_rows
        }

        planets = {}

        all_past = []

        all_future = []

        for planet_name in PLANET_ORDER:
            sides = (
                _three_transits_each_side(
                    now,
                    planet_name
                )
            )

            planets[
                planet_name
            ] = {
                "past":
                    sides["past"],

                "current":
                    current_by_planet[
                        planet_name
                    ],

                "future":
                    sides["future"]
            }

            all_past.extend(
                sides["past"]
            )

            all_future.extend(
                sides["future"]
            )

        all_past.sort(
            key=lambda x:
                x["timestamp"],
            reverse=True
        )

        all_future.sort(
            key=lambda x:
                x["timestamp"]
        )

        response = jsonify({
            "success": True,

            "updated_at":
                now.astimezone(
                    IST
                ).isoformat(),

            "timezone":
                "Asia/Kolkata",

            "data": {
                "past":
                    all_past,

                "current":
                    current_rows,

                "future":
                    all_future,

                "planets":
                    planets
            }
        })

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# KUNDALI API
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
                or
                {}
            )
        else:
            data = request.args

        date_str = (
            data.get("dob")
            or
            data.get("date")
        )

        time_str = data.get(
            "time"
        )

        person_name = data.get(
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

        sun_lon, sun_speed = (
            sidereal_position(
                jd,
                swe.SUN
            )
        )

        moon_lon, moon_speed = (
            sidereal_position(
                jd,
                swe.MOON
            )
        )

        planet_data = {}

        for planet_name in PLANET_ORDER:
            if planet_name == "केतु":
                continue

            planet_id = PLANET_IDS[
                planet_name
            ]

            longitude, speed = (
                sidereal_position(
                    jd,
                    planet_id
                )
            )

            planet_data[
                planet_name
            ] = planet_record(
                planet_name,
                longitude,
                speed,
                sun_lon
            )

        rahu_lon = planet_data[
            "राहु"
        ]["longitude"]

        ketu_lon = normalize(
            rahu_lon + 180.0
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

        for house_num in range(1, 13):
            sign_idx = (
                asc_rashi +
                house_num -
                1
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

                "planets":
                    []
            })

        for p_name in PLANET_ORDER:
            p = planet_data[
                p_name
            ]

            h = (
                house_from_equal_whole_sign(
                    p["longitude"],
                    asc_lon
                )
            )

            houses[
                h - 1
            ]["planets"].append({
                "name":
                    p_name,

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
            nak_lord,
            namakshara
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
            "name":
                person_name,

            "date":
                date_str,

            "time":
                time_str,

            "city":
                city,

            "latitude":
                lat,

            "longitude":
                lon
        }

        dasha = (
            calculate_vimshottari(
                birth_dt,
                moon_lon
            )
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

                "namakshara":
                    namakshara,

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

            "planet_order":
                PLANET_ORDER,

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


@app.get("/api/dasha")
def dasha_api():
    try:
        date_str = (
            request.args.get("date")
            or
            request.args.get("dob")
        )

        time_str = request.args.get(
            "time"
        )

        _, lat, lon = parse_location(
            request.args
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


@app.get("/api/location")
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
                    "Enter a valid Indian "
                    "PIN, Post Office or "
                    "City name"
            }), 400

        return jsonify({
            "success": True,

            "results":
                location_search(
                    q
                )
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/api/planet-order")
def planet_order_api():
    return jsonify({
        "success": True,

        "order":
            PLANET_ORDER,

        "order_hindi":
            "सूर्य → चंद्र → मंगल → बुध → "
            "गुरु → शुक्र → शनि → राहु → केतु"
    })


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
