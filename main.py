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
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी",
    "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी",
    "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी",
    "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी",
    "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

YOGA_NAMES = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड",
    "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि", "ध्रुव", "व्याघात",
    "हर्षण", "वज्र", "सिद्धि", "व्यतीपात", "वरीयान", "परिघ", "शिव",
    "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म", "ऐन्द्र", "वैधृति"
]

KARANA_FIXED = {
    0: "किंस्तुघ्न",
    57: "शकुनि",
    58: "चतुष्पाद",
    59: "नाग"
}
KARANA_MOVING = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि"]

WEEKDAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]

HINDI_MONTHS = [
    "चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद",
    "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"
]

PLANET_IDS = {
    "सूर्य": swe.SUN,
    "चंद्र": swe.MOON,
    "मंगल": swe.MARS,
    "बुध": swe.MERCURY,
    "गुरु": swe.JUPITER,
    "शुक्र": swe.VENUS,
    "शनि": swe.SATURN,
    "राहु": swe.MEAN_NODE,
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
    "बुध": 17.0,
}

DASHA_ORDER = ["केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"]

NAKSHATRA_LORDS = [
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"
]

RASHI_LORDS = [
    "मंगल", "शुक्र", "बुध", "चंद्र", "सूर्य", "बुध",
    "शुक्र", "मंगल", "गुरु", "शनि", "शनि", "गुरु"
]

YONI = [
    "अश्व", "गज", "मेष", "सर्प", "सर्प", "श्वान", "मार्जार", "मेष", "मार्जार",
    "मूषक", "मूषक", "गौ", "महिष", "व्याघ्र", "महिष", "व्याघ्र", "मृग",
    "मृग", "श्वान", "वानर", "नकुल", "वानर", "अश्व", "गज", "अश्व",
    "सिंह", "गौ"
]

GANA = [
    "देव", "मनुष्य", "राक्षस", "मनुष्य", "देव", "मनुष्य", "देव", "देव", "राक्षस",
    "राक्षस", "मनुष्य", "मनुष्य", "देव", "राक्षस", "देव", "राक्षस", "देव",
    "राक्षस", "राक्षस", "मनुष्य", "मनुष्य", "देव", "राक्षस", "राक्षस", "मनुष्य",
    "मनुष्य", "देव"
]

NADI = [
    "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि", "मध्य", "अन्त्य",
    "अन्त्य", "मध्य", "आदि", "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य",
    "आदि", "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि",
    "मध्य", "अन्त्य"
]

VARNA_BY_RASHI = {
    0: "क्षत्रिय", 1: "वैश्य", 2: "शूद्र", 3: "ब्राह्मण",
    4: "क्षत्रिय", 5: "वैश्य", 6: "शूद्र", 7: "ब्राह्मण",
    8: "क्षत्रिय", 9: "वैश्य", 10: "शूद्र", 11: "ब्राह्मण"
}

# ============================================================
# BASIC HELPERS
# ============================================================
def get_julian_day(local_dt):
    utc_dt = local_dt.astimezone(pytz.utc)
    return swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
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
    return IST.localize(dt.datetime(y, m, d, hh, mm, ss))

# ============================================================
# LOCATION / INDIA POST PINCODE
# ============================================================
LOCATION_CACHE = {}

def _http_json(url, timeout=12):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HindiPanchang-Kundali/2.1",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def india_post_search(query):
    query = (query or "").strip()
    if not query:
        return []

    # The public PostOffice endpoint returns the Indian postal
    # master information (post-office, district, state, pincode).
    url = "https://api.postalpincode.in/PostOffice/" + urllib.parse.quote(query)
    data = _http_json(url)
    if not data or data[0].get("Status") != "Success":
        return []

    result = []
    for po in data[0].get("PostOffice") or []:
        result.append({
            "display_name": "{}, {}, {} - {}".format(
                po.get("Name", ""),
                po.get("District", ""),
                po.get("State", ""),
                po.get("Pincode", "")
            ),
            "post_office": po.get("Name", ""),
            "city": po.get("District") or po.get("Name") or "",
            "district": po.get("District", ""),
            "state": po.get("State", ""),
            "pincode": str(po.get("Pincode", "")),
            "country": "India"
        })
    return result

def geocode_india_post_result(item):
    key = (item.get("post_office"), item.get("pincode"), item.get("district"), item.get("state"))
    if key in LOCATION_CACHE:
        return LOCATION_CACHE[key]

    queries = []
    if item.get("pincode"):
        queries.append(item["pincode"] + ", India")
    if item.get("post_office"):
        queries.append(item["post_office"] + ", " + item.get("district", "") + ", " + item.get("state", "") + ", India")

    for q in queries:
        params = urllib.parse.urlencode({
            "q": q, "format": "jsonv2", "addressdetails": 1,
            "limit": 5, "countrycodes": "in"
        })
        url = "https://nominatim.openstreetmap.org/search?" + params
        try:
            items = _http_json(url)
        except Exception:
            continue
        if items:
            # Prefer a result that contains the requested postcode.
            chosen = next((x for x in items if x.get("address", {}).get("postcode") == item.get("pincode")), items[0])
            try:
                item["latitude"] = float(chosen["lat"])
                item["longitude"] = float(chosen["lon"])
                item["display_name"] = item["display_name"]
                LOCATION_CACHE[key] = item
                return item
            except (KeyError, TypeError, ValueError):
                pass

    return None

def location_search(query):
    query = (query or "").strip()
    if not query:
        return []

    # Six-digit input: India Post data is authoritative for the postal
    # identity. Coordinates are then resolved separately.
    postal_results = india_post_search(query)
    if postal_results:
        result = []
        for item in postal_results[:12]:
            geo = geocode_india_post_result(item)
            if geo and "latitude" in geo:
                result.append(geo)
        return result

    # For city/post-office text, first search India Post's postal master.
    # This keeps displayed office/district/state/pincode synchronized with
    # postal data instead of taking those fields from a generic geocoder.
    try:
        postal_results = india_post_search(query)
    except Exception:
        postal_results = []

    result = []
    for item in postal_results[:12]:
        geo = geocode_india_post_result(item)
        if geo and "latitude" in geo:
            result.append(geo)
    if result:
        return result

    # Last fallback: city search, but still only for coordinate discovery.
    params = urllib.parse.urlencode({
        "q": query + ", India", "format": "jsonv2",
        "addressdetails": 1, "limit": 8, "countrycodes": "in"
    })
    url = "https://nominatim.openstreetmap.org/search?" + params
    items = _http_json(url)
    for item in items:
        address = item.get("address", {})
        result.append({
            "display_name": item.get("display_name", ""),
            "post_office": address.get("postcode", ""),
            "city": address.get("city") or address.get("town") or address.get("village") or address.get("municipality") or address.get("county") or "",
            "district": address.get("state_district", ""),
            "state": address.get("state", ""),
            "pincode": address.get("postcode", ""),
            "country": address.get("country", "India"),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"])
        })
    return result

def parse_location(source):
    city = source.get("city") or DEFAULT_CITY
    lat_value = source.get("lat")
    lon_value = source.get("lon")

    try:
        if lat_value is not None and lon_value is not None:
            return city, float(lat_value), float(lon_value)
    except (TypeError, ValueError):
        pass

    # Never silently use Ujjain when the user supplied a location query.
    # Resolve it through the same location service used by the UI.
    query = source.get("pincode") or source.get("location") or city
    try:
        matches = location_search(query)
        if matches:
            m = matches[0]
            return m.get("display_name") or m.get("city") or city, float(m["latitude"]), float(m["longitude"])
    except Exception:
        pass

    return DEFAULT_CITY, DEFAULT_LAT, DEFAULT_LON

def degree_text(lon):
    local = lon % 30.0
    deg = int(local)
    minute_float = (local - deg) * 60.0
    minute = int(minute_float)
    second = int(round((minute_float - minute) * 60))
    if second == 60:
        second = 0
        minute += 1
    if minute >= 60:
        minute = 0
        deg += 1
    return f"{deg}°{minute:02d}'{second:02d}\""

def nakshatra_info(lon):
    span = 360.0 / 27.0
    idx = min(26, int(normalize(lon) / span))
    within = normalize(lon) - idx * span
    pada = min(4, int(within / (span / 4.0)) + 1)
    return idx, NAKSHATRA_NAMES[idx], pada, NAKSHATRA_LORDS[idx]

def rashi_index(lon):
    return int(normalize(lon) / 30.0) % 12

def sidereal_position(jd, planet_id, with_speed=True):
    flags = swe.FLG_SIDEREAL
    if with_speed:
        flags |= swe.FLG_SPEED
    pos, _ = swe.calc_ut(jd, planet_id, flags)
    return normalize(pos[0]), pos[3]

def safe_date_text(value):
    return value.strftime("%d-%m-%Y")

# ============================================================
# PANCHANG HELPERS
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
    observer.date = IST.localize(dt.datetime(y, m, d, 0, 5)).astimezone(pytz.utc)

    sun = ephem.Sun()
    try:
        value = observer.next_rising(sun) if rising else observer.next_setting(sun)
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
    observer.date = IST.localize(dt.datetime(y, m, d, 0, 5)).astimezone(pytz.utc)
    moon = ephem.Moon()
    try:
        value = observer.next_rising(moon) if rising else observer.next_setting(moon)
        value_dt = value.datetime()
        if value_dt.tzinfo is None:
            value_dt = pytz.utc.localize(value_dt)
        return value_dt.astimezone(IST)
    except Exception:
        return None

def event_time_text(value, base_date):
    if not value:
        return "--"
    suffix = "अगले दिन " if value.date() > base_date else ""
    return suffix + value.strftime("%I:%M %p")

def panchang_for_date(date_str, city, lat, lon):
    y, m, d = map(int, date_str.split("-"))
    local_dt = IST.localize(dt.datetime(y, m, d, 12, 0))
    jd = get_julian_day(local_dt)

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun_lon, sun_speed = sidereal_position(jd, swe.SUN)
    moon_lon, moon_speed = sidereal_position(jd, swe.MOON)

    angle_diff = normalize(moon_lon - sun_lon)
    tithi_position = angle_diff / 12.0
    tithi_idx = min(29, int(tithi_position))
    paksha = "शुक्ल पक्ष" if tithi_idx < 15 else "कृष्ण पक्ष"

    rel_speed = moon_speed - sun_speed
    tithi_end = None
    if rel_speed > 0:
        degrees_left = ((tithi_idx + 1) * 12.0) - angle_diff
        end_jd = jd + degrees_left / rel_speed
        y2, m2, d2, h2 = swe.revjul(end_jd, swe.GREG_CAL)
        utc_end = pytz.utc.localize(
            dt.datetime(y2, m2, d2) + dt.timedelta(hours=h2)
        )
        tithi_end = utc_end.astimezone(IST)

    nak_idx, nak_name, nak_pada, nak_lord = nakshatra_info(moon_lon)
    yoga_idx = int(normalize(sun_lon + moon_lon) / (360.0 / 27.0))
    yoga_idx = min(26, yoga_idx)

    karana_position = angle_diff / 6.0
    karana_idx = int(karana_position)
    karan_1 = karana_name(karana_idx)
    karan_2 = karana_name((karana_idx + 1) % 60)

    sun_rashi_idx = rashi_index(sun_lon)
    moon_rashi_idx = rashi_index(moon_lon)

    # This preserves the original project's simple month convention.
    # It is not a full drik month calculation.
    vikram = y + 57
    shaka = y - 78
    kali = y + 3101

    sunrise_dt = find_sun_event(y, m, d, lat, lon, True)
    sunset_dt = find_sun_event(y, m, d, lat, lon, False)
    moonrise_dt = moon_event(y, m, d, lat, lon, True)
    moonset_dt = moon_event(y, m, d, lat, lon, False)

    ayan = "उत्तरायण" if sun_rashi_idx in [9, 10, 11, 0, 1, 2] else "दक्षिणायन"
    ritu_map = {
        11: "वसंत", 0: "वसंत", 1: "ग्रीष्म", 2: "ग्रीष्म",
        3: "वर्षा", 4: "वर्षा", 5: "शरद", 6: "शरद",
        7: "हेमंत", 8: "हेमंत", 9: "शिशिर", 10: "शिशिर"
    }

    # Ishta Kaal is traditionally sunrise-based. We expose the raw
    # approximate clock value here; a full traditional ghati calculation
    # can be added later without changing the API structure.
    ishta_kaal = "--"
    if sunrise_dt:
        noon_dt = IST.localize(dt.datetime(y, m, d, 12, 0))
        minutes = max(0, int((noon_dt - sunrise_dt).total_seconds() / 60))
        ghati = minutes // 24
        pala = int((minutes % 24) * 2.5)
        ishta_kaal = f"{ghati} घटी {pala} पल"

    return {
        "success": True,
        "data": {
            "location": {
                "city": city,
                "latitude": lat,
                "longitude": lon
            },
            "summary_header": f"{TITHI_NAMES[tithi_idx]}, {nak_name} नक्षत्र",
            "details": {
                "tithi": TITHI_NAMES[tithi_idx],
                "tithi_end_time": event_time_text(tithi_end, local_dt.date()),
                "paksha": paksha,
                "nakshatra": nak_name,
                "nakshatra_pada": nak_pada,
                "nakshatra_lord": nak_lord,
                "yog": YOGA_NAMES[yoga_idx],
                "karan_1": karan_1,
                "karan_2": karan_2,
                "var": WEEKDAYS[local_dt.weekday()],
                "chandra_rashi": RASHI_NAMES[moon_rashi_idx],
                "surya_rashi": RASHI_NAMES[sun_rashi_idx],
                "vikram_samvat": str(vikram),
                "shaka_samvat": str(shaka),
                "kali_samvat": str(kali),
                "ayan": ayan,
                "ritu": ritu_map.get(sun_rashi_idx, "--"),
                "maah_purnimant": HINDI_MONTHS[(sun_rashi_idx + 1) % 12],
                "ishta_kaal": ishta_kaal
            },
            "timings": {
                "sunrise": sunrise_dt.strftime("%I:%M %p") if sunrise_dt else "--",
                "sunset": sunset_dt.strftime("%I:%M %p") if sunset_dt else "--",
                "chandrodaya": moonrise_dt.strftime("%I:%M %p") if moonrise_dt else "--",
                "chandrast": moonset_dt.strftime("%I:%M %p") if moonset_dt else "--"
            }
        }
    }

# ============================================================
# KUNDALI HELPERS
# ============================================================
def planet_record(name, lon, speed, sun_lon):
    r_idx = rashi_index(lon)
    n_idx, n_name, n_pada, n_lord = nakshatra_info(lon)

    is_asta = False
    if name not in ["सूर्य", "चंद्र", "राहु", "केतु"]:
        diff = abs(lon - sun_lon)
        if diff > 180:
            diff = 360 - diff
        is_asta = diff <= 8.5

    return {
        "name": name,
        "longitude": round(lon, 6),
        "rashi": RASHI_NAMES[r_idx],
        "rashi_num": r_idx + 1,
        "degree": degree_text(lon),
        "nakshatra": n_name,
        "nakshatra_pada": n_pada,
        "nakshatra_lord": n_lord,
        "is_vakri": bool(speed < 0),
        "is_asta": bool(is_asta)
    }

def calculate_houses(jd, lat, lon):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    try:
        cusps, ascmc = swe.houses_ex(
            jd, lat, lon, b"P", swe.FLG_SIDEREAL
        )
        asc = normalize(ascmc[0])
        # houses_ex with sidereal flag returns sidereal cusps.
        cusp_list = [normalize(cusps[i]) for i in range(12)]
        return asc, cusp_list
    except Exception:
        # Fallback preserving compatibility with older pyswisseph builds.
        cusps, ascmc = swe.houses(jd, lat, lon, b"P")
        ayan = swe.get_ayanamsa_ut(jd)
        asc = normalize(ascmc[0] - ayan)
        cusp_list = [normalize(c - ayan) for c in cusps[:12]]
        return asc, cusp_list

def house_from_equal_whole_sign(lon, asc_lon):
    # North-Indian Vedic chart is commonly represented as whole-sign houses:
    # the Lagna rashi is house 1, next rashi house 2, etc.
    return ((rashi_index(lon) - rashi_index(asc_lon)) % 12) + 1

def manglik_status(mars_rashi, asc_rashi):
    house = ((mars_rashi - asc_rashi) % 12) + 1
    # Common Lagna-based Manglik convention: 1, 4, 7, 8, 12.
    is_manglik = house in [1, 4, 7, 8, 12]
    return {
        "is_manglik": is_manglik,
        "status": "मांगलिक है" if is_manglik else "मांगलिक नहीं",
        "mars_house_from_lagna": house
    }

# ============================================================
# VIMSHOTTARI DASHA
# ============================================================
def add_years(base_date, years):
    # Tropical Gregorian calendar year fraction used only for dasha display.
    days = years * 365.2425
    return base_date + dt.timedelta(days=days)

def dasha_sequence(start_lord):
    idx = DASHA_ORDER.index(start_lord)
    return DASHA_ORDER[idx:] + DASHA_ORDER[:idx]

def build_antardashas(maha_lord, maha_start, maha_end, now):
    total_maha_days = (maha_end - maha_start).total_seconds() / 86400.0
    result = []
    cursor = maha_start

    for lord in dasha_sequence(maha_lord):
        duration_days = total_maha_days * DASHA_YEARS[lord] / 120.0
        end = cursor + dt.timedelta(days=duration_days)
        result.append({
            "planet": lord,
            "start": cursor.strftime("%d-%m-%Y"),
            "end": end.strftime("%d-%m-%Y"),
            "current": cursor <= now < end
        })
        cursor = end

    return result

def calculate_vimshottari(dob_local, moon_lon):
    nak_idx, nak_name, pada, nak_lord = nakshatra_info(moon_lon)
    span = 360.0 / 27.0
    nak_start = nak_idx * span
    travelled = normalize(moon_lon) - nak_start
    fraction_completed = max(0.0, min(1.0, travelled / span))

    first_lord = nak_lord
    first_years_remaining = DASHA_YEARS[first_lord] * (1.0 - fraction_completed)

    birth_date = dob_local
    cursor = birth_date
    now = dt.datetime.now(IST)

    mahadashas = []
    first = True

    while len(mahadashas) < 18:
        lord = first_lord if first else DASHA_ORDER[
            (DASHA_ORDER.index(first_lord) + len(mahadashas)) % 9
        ]
        years = first_years_remaining if first else DASHA_YEARS[lord]
        end = add_years(cursor, years)

        mahadashas.append({
            "planet": lord,
            "start": cursor.strftime("%d-%m-%Y"),
            "end": end.strftime("%d-%m-%Y"),
            "years": round(years, 4),
            "current": cursor <= now < end,
            "antardasha": build_antardashas(lord, cursor, end, now)
        })

        cursor = end
        first = False

    current_maha = next((x for x in mahadashas if x["current"]), None)

    return {
        "nakshatra": nak_name,
        "nakshatra_pada": pada,
        "starting_mahadasha": first_lord,
        "current_mahadasha": current_maha["planet"] if current_maha else None,
        "mahadasha": mahadashas
    }

@app.get("/api/pincode")
def pincode_api():
    try:
        q = request.args.get("q", "").strip()
        if len(q) < 3:
            return jsonify({"success": False, "error": "Enter PIN code or post office name"}), 400
        return jsonify({"success": True, "results": location_search(q)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# ROUTES
# ============================================================
@app.get("/")
def home():
    return jsonify({
        "success": True,
        "service": "Hindi Panchang & Kundali API",
        "status": "online",
        "version": "2.0",
        "endpoints": [
            "/health",
            "/api/full-panchang-hindi?date=YYYY-MM-DD&city=Ujjain&lat=23.1765&lon=75.7885",
            "/api/generate-kundali?date=YYYY-MM-DD&time=HH:MM&city=Ujjain&lat=23.1765&lon=75.7885",
            "/api/location?q=Ujjain",
            "/api/dasha?date=YYYY-MM-DD&time=HH:MM&lat=23.1765&lon=75.7885"
        ]
    })

@app.get("/health")
def health():
    return jsonify({"success": True, "status": "healthy"})

@app.get("/api/full-panchang-hindi")
@app.get("/api/full-panchang-hindi-fix")
def get_panchang():
    try:
        date_str = request.args.get("date")
        city, lat, lon = parse_location(request.args)
        if not date_str:
            return jsonify({"success": False, "error": "Date is required"}), 400
        return jsonify(panchang_for_date(date_str, city, lat, lon))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/generate-kundali", methods=["GET", "POST"])
def generate_kundali():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
        else:
            data = request.args

        date_str = data.get("dob") or data.get("date")
        time_str = data.get("time")
        name = data.get("name", "")
        city, lat, lon = parse_location(data)

        birth_dt = parse_date_time(date_str, time_str)
        jd = get_julian_day(birth_dt)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        sun_lon, _ = sidereal_position(jd, swe.SUN)
        moon_lon, moon_speed = sidereal_position(jd, swe.MOON)

        planet_data = {}
        for name_key, p_id in PLANET_IDS.items():
            lon_value, speed = sidereal_position(jd, p_id)
            planet_data[name_key] = planet_record(
                name_key, lon_value, speed, sun_lon
            )

        ketu_lon = normalize(planet_data["राहु"]["longitude"] + 180.0)
        planet_data["केतु"] = planet_record(
            "केतु", ketu_lon, -1.0, sun_lon
        )

        asc_lon, cusp_list = calculate_houses(jd, lat, lon)
        asc_rashi = rashi_index(asc_lon)

        # Whole-sign house placement for the North Indian Vedic chart.
        houses = []
        for house_num in range(1, 13):
            sign_idx = (asc_rashi + house_num - 1) % 12
            houses.append({
                "house": house_num,
                "rashi": RASHI_NAMES[sign_idx],
                "rashi_num": sign_idx + 1,
                "planets": []
            })

        for p_name, p in planet_data.items():
            h = house_from_equal_whole_sign(p["longitude"], asc_lon)
            houses[h - 1]["planets"].append({
                "name": p_name,
                "vakri": p["is_vakri"],
                "asta": p["is_asta"]
            })
            p["house"] = h

        nak_idx, nak_name, nak_pada, nak_lord = nakshatra_info(moon_lon)
        moon_rashi = rashi_index(moon_lon)

        # Birth Panchang is calculated for the birth date and exact location.
        panchang = panchang_for_date(date_str, city, lat, lon)["data"]

        mars_rashi = rashi_index(planet_data["मंगल"]["longitude"])
        manglik = manglik_status(mars_rashi, asc_rashi)

        birth_details = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "city": city,
            "latitude": lat,
            "longitude": lon
        }

        dasha = calculate_vimshottari(birth_dt, moon_lon)

        # Paya convention based on Janma Nakshatra/Rashi.
        # Silver/Gem/Gold/Iron is exposed as a separate field so the UI
        # can display it without changing the rest of the response.
        paya_map = {0: "स्वर्ण", 1: "रजत", 2: "ताम्र", 3: "लोह"}
        paya = paya_map.get(moon_rashi % 4, "रजत")

        return jsonify({
            "success": True,
            "birth_details": birth_details,
            "lagna": {
                "rashi": RASHI_NAMES[asc_rashi],
                "rashi_num": asc_rashi + 1,
                "degree": degree_text(asc_lon),
                "longitude": round(asc_lon, 6)
            },
            "basic": {
                "rashi": RASHI_NAMES[moon_rashi],
                "rashi_lord": RASHI_LORDS[moon_rashi],
                "janma_nakshatra": nak_name,
                "nakshatra_pada": nak_pada,
                "nakshatra_lord": nak_lord,
                "paya": paya,
                "yoni": YONI[nak_idx],
                "gana": GANA[nak_idx],
                "nadi": NADI[nak_idx],
                "varna": VARNA_BY_RASHI[moon_rashi],
                "manglik": manglik
            },
            "panchang": panchang,
            "planets": planet_data,
            "houses": houses,
            "chart": {
                "type": "north_indian",
                "style": "whole_sign",
                "ascendant_house": 1,
                "houses": houses
            },
            "dasha": dasha
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/dasha")
def dasha_api():
    try:
        date_str = request.args.get("date") or request.args.get("dob")
        time_str = request.args.get("time")
        _, lat, lon = parse_location(request.args)

        birth_dt = parse_date_time(date_str, time_str)
        jd = get_julian_day(birth_dt)
        moon_lon, _ = sidereal_position(jd, swe.MOON)

        return jsonify({
            "success": True,
            "data": calculate_vimshottari(birth_dt, moon_lon)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/location")
def location_api():
    try:
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return jsonify({
                "success": False,
                "error": "Enter city or pincode"
            }), 400

        return jsonify({
            "success": True,
            "results": location_search(q)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================
# SERVER
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
