from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import swisseph as swe
from datetime import datetime, timedelta
import urllib.request
import json

app = FastAPI()

# Root endpoint for Render/UptimeRobot
# Supports both GET and HEAD requests.
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "ok",
        "message": "Pandit JI Backend is running"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TITHIS_SHUKLA = [
    "शुक्ल प्रतिपदा", "शुक्ल द्वितीया", "शुक्ल तृतीया", "शुक्ल चतुर्थी", "शुक्ल पंचमी",
    "शुक्ल षष्ठी", "शुक्ल सप्तमी", "शुक्ल अष्टमी", "शुक्ल नवमी", "शुक्ल दशमी",
    "शुक्ल एकादशी", "शुक्ल द्वादशी", "शुक्ल त्रयोदशी", "शुक्ल चतुर्दशी", "पूर्णिमा"
]

TITHIS_KRISHNA = [
    "कृष्ण प्रतिपदा", "कृष्ण द्वितीया", "कृष्ण तृतीया", "कृष्ण चतुर्थी", "कृष्ण पंचमी",
    "कृष्ण षष्ठी", "कृष्ण सप्तमी", "कृष्ण अष्टमी", "कृष्ण नवमी", "कृष्ण दशमी",
    "कृष्ण एकादशी", "कृष्ण द्वादशी", "कृष्ण त्रयोदशी", "कृष्ण चतुर्दशी", "अमावस्या"
]

NAKSHATRAS = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "अश्लेषा", "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी",
    "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा",
    "मूल", "पूर्वाषाढा", "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शतभिषा",
    "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती"
]

RASHIS = [
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
]

YOGS = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड",
    "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि", "ध्रुव",
    "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात", "वरीयान",
    "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ", "शुक्ल",
    "ब्रह्म", "ऐन्द्र", "वैधृति"
]

KARANS = [
    "बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज",
    "विष्टि", "शकुनि", "चतुष्पाद", "नाग", "किंतुघ्न"
]

HINDI_DAYS = [
    "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"
]

NAMAKSHARS = [
    ["चू", "चे", "चो", "ला"], ["ली", "लू", "ले", "लो"], ["अ", "ई", "उ", "ए"], ["ओ", "वा", "वी", "वू"],
    ["वे", "वो", "का", "की"], ["कू", "घ", "ङ", "छ"], ["के", "को", "हा", "ही"], ["हू", "हे", "हो", "डा"],
    ["डी", "डू", "डे", "डो"], ["मा", "मी", "मू", "मे"], ["मो", "टा", "टी", "टू"], ["टे", "टो", "पा", "पी"],
    ["पू", "ष", "ण", "ठ"], ["पे", "पो", "रा", "री"], ["रू", "रे", "रो", "ता"], ["ती", "तू", "ते", "तो"],
    ["ना", "नी", "नू", "ने"], ["नो", "या", "यी", "यू"], ["ये", "यो", "भा", "भी"], ["भू", "धा", "फा", "ढा"],
    ["भे", "भो", "जा", "जी"], ["खी", "खू", "खे", "खो"], ["गा", "गी", "गू", "गे"], ["गो", "सा", "सी", "सू"],
    ["से", "सो", "दा", "दी"], ["दू", "थ", "झ", "ञ"], ["दे", "दो", "च", "ची"]
]

DASHA_LORDS = [
    ("केतु", 7), ("शुक्र", 20), ("सूर्य", 6), ("चन्द्र", 10),
    ("मंगल", 7), ("राहु", 18), ("गुरु", 16), ("शनि", 19), ("बुध", 17)
]

HINDI_MONTHS = [
    "चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़",
    "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक",
    "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"
]

KNOWN_CITIES = {
    "ujjain": {"lat": 23.1765, "lon": 75.7885, "tz": 5.5},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "tz": 5.5},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "tz": 5.5},
    "varanasi": {"lat": 25.3176, "lon": 82.9739, "tz": 5.5},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "tz": 5.5},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "tz": 5.5},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "tz": 5.5},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "tz": 5.5},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "tz": 5.5},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "tz": 5.5},
    "pune": {"lat": 18.5204, "lon": 73.8567, "tz": 5.5},
    "indore": {"lat": 22.7196, "lon": 75.8577, "tz": 5.5},
    "bhopal": {"lat": 23.2599, "lon": 77.4126, "tz": 5.5},
    "patna": {"lat": 25.5941, "lon": 85.1376, "tz": 5.5}
}


def resolve_location_coordinates(
    loc_input: str,
    lat_override: float = None,
    lon_override: float = None
):
    if lat_override is not None and lon_override is not None:
        return lat_override, lon_override, 5.5, "Custom Coordinates"

    clean_input = (loc_input or "ujjain").strip()

    city_match = KNOWN_CITIES.get(
        clean_input.lower(),
        {"lat": 23.1765, "lon": 75.7885, "tz": 5.5}
    )

    return (
        city_match["lat"],
        city_match["lon"],
        city_match["tz"],
        clean_input.title()
    )


def _find_amavasya_jd(jd, find_next=False):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    step = 0.5 if find_next else -0.5
    curr = jd
    for _ in range(70):
        s_pos, _ = swe.calc_ut(curr, swe.SUN, swe.FLG_SIDEREAL)
        m_pos, _ = swe.calc_ut(curr, swe.MOON, swe.FLG_SIDEREAL)
        diff = (m_pos[0] - s_pos[0]) % 360.0
        if find_next and diff < 15.0:
            break
        elif not find_next and diff > 345.0:
            break
        curr += step

    low = curr - abs(step)
    high = curr + abs(step)
    for _ in range(25):
        mid = (low + high) / 2.0
        s_pos, _ = swe.calc_ut(mid, swe.SUN, swe.FLG_SIDEREAL)
        m_pos, _ = swe.calc_ut(mid, swe.MOON, swe.FLG_SIDEREAL)
        diff = (m_pos[0] - s_pos[0]) % 360.0
        if diff > 180.0:
            diff -= 360.0
        if diff > 0:
            if find_next:
                high = mid
            else:
                low = mid
        else:
            if find_next:
                low = mid
            else:
                high = mid
    return (low + high) / 2.0


def calculate_purnimanta_month(sun_lon, moon_lon, jd=None):
    # Purnimanta month logic copied from the verified Panchang backend.
    # The month is determined from the Amavasya-to-Amavasya solar rashi,
    # then Krishna Paksha is assigned to the following Purnimanta month.
    angle_diff = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(angle_diff / 12.0)

    if jd is not None:
        try:
            prev_amav_jd = _find_amavasya_jd(jd, find_next=False)
            next_amav_jd = _find_amavasya_jd(jd, find_next=True)

            s_prev, _ = swe.calc_ut(
                prev_amav_jd, swe.SUN, swe.FLG_SIDEREAL
            )
            s_next, _ = swe.calc_ut(
                next_amav_jd, swe.SUN, swe.FLG_SIDEREAL
            )

            r_start = int(s_prev[0] / 30.0) % 12
            r_end = int(s_next[0] / 30.0) % 12

            # Same solar rashi at both Amavasyas = Adhik Maas.
            is_adhik = (r_start == r_end)

            # Amanta month starts from the solar rashi following the
            # previous Amavasya. Convert it to Purnimanta month.
            amanta_idx = (r_start + 1) % 12

            # Purnimanta month changes at Krishna Pratipada.
            if tithi_idx >= 15:
                purnimant_idx = (amanta_idx + 1) % 12
            else:
                purnimant_idx = amanta_idx

            name = HINDI_MONTHS[purnimant_idx]
            return (
                f"अधिक {name}" if is_adhik else name,
                purnimant_idx
            )
        except Exception:
            pass

    # Safe fallback when Julian day is unavailable.
    sun_rashi = int((sun_lon % 360.0) / 30.0) % 12
    amanta_idx = (sun_rashi + 1) % 12
    purnimant_idx = (amanta_idx + 1) % 12 if tithi_idx >= 15 else amanta_idx
    return HINDI_MONTHS[purnimant_idx], purnimant_idx


@app.get("/api/generate-kundali")
def generate_kundali(
    name: str = "User",
    dob: str = "2026-01-01",
    time: str = "12:00",
    city: str = "Ujjain",
    lat: float = None,
    lon: float = None
):
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        resolved_lat, resolved_lon, tz, resolved_loc = resolve_location_coordinates(
            city,
            lat,
            lon
        )

        time_str = (time or "12:00").strip()

        if len(time_str.split(':')) == 2:
            time_str += ":00"

        dt = datetime.strptime(
            f"{dob} {time_str}",
            "%Y-%m-%d %H:%M:%S"
        )

        ut_hour = (
            dt.hour
            + dt.minute / 60.0
            + dt.second / 3600.0
            - tz
        )

        jd_ut = swe.julday(
            dt.year,
            dt.month,
            dt.day,
            ut_hour
        )

        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH

        cusps, ascmc = swe.houses_ex(
            jd_ut,
            resolved_lat,
            resolved_lon,
            b'A',
            flags
        )

        lagna_deg = ascmc[0] % 360
        lagna_rashi_idx = int(lagna_deg // 30)

        lagna_deg_in_sign = lagna_deg % 30

        lagna_deg_str = (
            f"{RASHIS[lagna_rashi_idx % len(RASHIS)]} "
            f"{int(lagna_deg_in_sign)}° "
            f"{int((lagna_deg_in_sign % 1) * 60)}'"
        )

        planets = {
            "सूर्य": swe.SUN,
            "चन्द्र": swe.MOON,
            "मंगल": swe.MARS,
            "बुध": swe.MERCURY,
            "गुरु": swe.JUPITER,
            "शुक्र": swe.VENUS,
            "शनि": swe.SATURN,
            "राहु": swe.MEAN_NODE
        }

        planet_data = {}
        house_planets = {i: [] for i in range(1, 13)}

        for p_name, p_code in planets.items():

            pos, ret = swe.calc_ut(
                jd_ut,
                p_code,
                flags | swe.FLG_SPEED
            )

            p_deg = pos[0] % 360
            p_speed = pos[3]

            r_idx = int(p_deg // 30)
            deg_in_sign = p_deg % 30

            deg_str = (
                f"{int(deg_in_sign)}° "
                f"{int((deg_in_sign % 1) * 60)}'"
            )

            h_num = (
                ((r_idx - lagna_rashi_idx) % 12) + 1
            )

            house_planets[h_num].append(p_name)

            is_vakri = (
                p_speed < 0
                and p_name not in ["सूर्य", "चन्द्र", "राहु", "केतु"]
            )

            planet_data[p_name] = {
                "name": p_name,
                "rashi": RASHIS[r_idx % len(RASHIS)],
                "rashi_idx": r_idx,
                "degree": deg_str,
                "house": h_num,
                "longitude": p_deg,
                "is_vakri": is_vakri,
                "is_asta": False
            }

        ketu_lon = (
            planet_data["राहु"]["longitude"] + 180
        ) % 360

        ketu_r_idx = int(ketu_lon // 30)
        ketu_deg = ketu_lon % 30

        ketu_h = (
            ((ketu_r_idx - lagna_rashi_idx) % 12) + 1
        )

        house_planets[ketu_h].append("केतु")

        planet_data["केतु"] = {
            "name": "केतु",
            "rashi": RASHIS[ketu_r_idx % len(RASHIS)],
            "rashi_idx": ketu_r_idx,
            "degree": (
                f"{int(ketu_deg)}° "
                f"{int((ketu_deg % 1) * 60)}'"
            ),
            "house": ketu_h,
            "longitude": ketu_lon,
            "is_vakri": True,
            "is_asta": False
        }

        moon_lon = planet_data["चन्द्र"]["longitude"]
        sun_lon = planet_data["सूर्य"]["longitude"]

        diff_deg = (
            moon_lon - sun_lon
        ) % 360

        if diff_deg >= 180.0:
            paksha = "कृष्ण पक्ष"
            tithi_idx = int(
                (diff_deg - 180.0) // 12
            ) % 15
            tithi_name = TITHIS_KRISHNA[tithi_idx]
        else:
            paksha = "शुक्ल पक्ष"
            tithi_idx = int(
                diff_deg // 12
            ) % 15
            tithi_name = TITHIS_SHUKLA[tithi_idx]

        moon_nak_idx = int(
            moon_lon // (360.0 / 27.0)
        ) % len(NAKSHATRAS)

        nak_deg_rem = (
            moon_lon % (360.0 / 27.0)
        )

        pada_idx = int(
            nak_deg_rem // (360.0 / 108.0)
        ) % 4

        namakshar = NAMAKSHARS[
            moon_nak_idx
        ][pada_idx]

        yog_sum = (
            sun_lon + moon_lon
        ) % 360

        yog_idx = int(
            yog_sum // (360.0 / 27.0)
        ) % len(YOGS)

        karan_idx = int(
            diff_deg // 6
        ) % len(KARANS)

        mars_house = planet_data["मंगल"]["house"]

        is_manglik = mars_house in [
            1, 4, 7, 8, 12
        ]

        manglik_desc = (
            f"मंगल {mars_house}वें भाव में स्थित है।"
            if is_manglik
            else "मंगल शुभ भावों में स्थित है।"
        )

        dasha_lord_index = (
            moon_nak_idx % 9
        ) % len(DASHA_LORDS)

        dasha_start_lord = (
            DASHA_LORDS[dasha_lord_index][0]
        )

        dasha_start_years = (
            DASHA_LORDS[dasha_lord_index][1]
        )

        moon_rashi_idx = (
            planet_data["चन्द्र"]["rashi_idx"]
        )

        saturn_rashi_idx = (
            planet_data["शनि"]["rashi_idx"]
        )

        sadesati_diff = (
            saturn_rashi_idx - moon_rashi_idx
        ) % 12

        if sadesati_diff in [11, 0, 1]:
            sati_status = (
                "सक्रिय (साढ़े साती चालू है)"
            )
        elif sadesati_diff in [3, 7]:
            sati_status = "शनि ढैय्या प्रभाव"
        else:
            sati_status = (
                "निष्क्रिय (कोई प्रभाव नहीं)"
            )

        chart_houses = {}

        for h in range(1, 13):

            r_num = (
                (lagna_rashi_idx + h - 1) % 12
            ) + 1

            p_names = ", ".join(
                house_planets[h]
            )

            chart_houses[f"h{h}"] = (
                f"{r_num} ({p_names})"
                if p_names
                else str(r_num)
            )

        formatted_planets = {}

        for p_name, p_info in planet_data.items():

            p_nak_idx = int(
                p_info["longitude"] /
                (360.0 / 27.0)
            ) % len(NAKSHATRAS)

            p_nak_rem = (
                p_info["longitude"] %
                (360.0 / 27.0)
            )

            p_pada_idx = int(
                p_nak_rem /
                (360.0 / 108.0)
            ) % 4

            formatted_planets[p_name] = {
                "rashi": p_info["rashi"],
                "degree": p_info["degree"],
                "nakshatra": NAKSHATRAS[p_nak_idx],
                "nakshatra_pada": (
                    f"चरण {p_pada_idx + 1}"
                ),
                "is_vakri": p_info["is_vakri"],
                "is_asta": p_info["is_asta"]
            }

        return {
            "success": True,

            "planet_order": [
                "सूर्य",
                "चंद्र",
                "मंगल",
                "बुध",
                "गुरु",
                "शुक्र",
                "शनि",
                "राहु",
                "केतु"
            ],

            "planets": formatted_planets,

            "data": {

                "resolved_location": resolved_loc,

                "birth_panchang": {
                    "var": HINDI_DAYS[
                        dt.weekday() % len(HINDI_DAYS)
                    ],

                    "tithi": tithi_name,

                    "nakshatra": (
                        f"{NAKSHATRAS[moon_nak_idx]} "
                        f"(पद {pada_idx + 1})"
                    ),

                    "namakshar": namakshar,

                    "yog": YOGS[yog_idx],

                    "karan": KARANS[karan_idx],

                    "chandra_rashi": (
                        planet_data["चन्द्र"]["rashi"]
                    ),

                    "surya_rashi": (
                        planet_data["सूर्य"]["rashi"]
                    ),

                    "lagna": (
                        RASHIS[
                            lagna_rashi_idx %
                            len(RASHIS)
                        ]
                    ),

                    "lagna_degree": lagna_deg_str
                },

                "chart_houses": chart_houses,

                "nirayana_planets": list(
                    planet_data.values()
                ),

                "manglik_info": {
                    "is_manglik": is_manglik,
                    "description": manglik_desc
                },

                "mahadasha_info": {
                    "current_mahadasha": dasha_start_lord,
                    "ends_at": (
                        f"{dt.year + dasha_start_years}"
                    )
                },

                "sadesati_info": {
                    "status": sati_status
                }
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/full-panchang-hindi")
def full_panchang_hindi(
    date: str,
    city: str = "Ujjain"
):
    try:

        swe.set_sid_mode(
            swe.SIDM_LAHIRI
        )

        lat, lon, tz, resolved_loc = (
            resolve_location_coordinates(
                city or "Ujjain"
            )
        )

        dt = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        geopos = (
            lon,
            lat,
            0
        )

        jd_midnight = swe.julday(
            dt.year,
            dt.month,
            dt.day,
            0.0
        )

        rise_result = swe.rise_trans(
            jd_midnight - (tz / 24.0),
            swe.SUN,
            swe.CALC_RISE,
            geopos,
            0,
            0
        )

        if rise_result[0] == 0:
            jd_sunrise = rise_result[1][0]
        else:
            jd_sunrise = (
                jd_midnight
                + (6.0 - tz) / 24.0
            )

        flags = (
            swe.FLG_SIDEREAL |
            swe.FLG_SWIEPH
        )

        sun_pos, _ = swe.calc_ut(
            jd_sunrise,
            swe.SUN,
            flags
        )

        moon_pos, _ = swe.calc_ut(
            jd_sunrise,
            swe.MOON,
            flags
        )

        sun_lon = sun_pos[0] % 360
        moon_lon = moon_pos[0] % 360

        diff_deg = (
            moon_lon - sun_lon
        ) % 360

        if diff_deg >= 180.0:

            paksha = "कृष्ण पक्ष"

            tithi_idx = int(
                (diff_deg - 180.0) // 12
            ) % 15

            tithi_name = (
                TITHIS_KRISHNA[tithi_idx]
            )

        else:

            paksha = "शुक्ल पक्ष"

            tithi_idx = int(
                diff_deg // 12
            ) % 15

            tithi_name = (
                TITHIS_SHUKLA[tithi_idx]
            )

        tithi_end_str = ""
        next_tithi_name = None
        next_tithi_end_str = None
        next_tithi_start_str = None

        try:

            for step in range(1, 50):

                test_jd = (
                    jd_sunrise
                    + (step * 0.25 / 24.0)
                )

                s_pos, _ = swe.calc_ut(
                    test_jd,
                    swe.SUN,
                    flags
                )

                m_pos, _ = swe.calc_ut(
                    test_jd,
                    swe.MOON,
                    flags
                )

                t_diff = (
                    m_pos[0] - s_pos[0]
                ) % 360

                if diff_deg >= 180.0:

                    curr_t_idx = (
                        int(
                            (t_diff - 180.0) // 12
                        ) % 15
                        if t_diff >= 180.0
                        else
                        int(t_diff // 12) % 15
                    )

                else:

                    curr_t_idx = (
                        int(t_diff // 12) % 15
                        if t_diff < 180.0
                        else
                        int(
                            (t_diff - 180.0) // 12
                        ) % 15
                    )

                if curr_t_idx != tithi_idx:

                    end_dt = datetime.fromtimestamp(
                        (
                            test_jd
                            + tz / 24.0
                            - 2440587.5
                        ) * 86400.0
                    )

                    tithi_end_str = (
                        end_dt.strftime(
                            "%I:%M %p"
                        )
                    )

                    if diff_deg >= 180.0:
                        next_tithi_name = (
                            TITHIS_KRISHNA[
                                curr_t_idx
                            ]
                        )
                    else:
                        next_tithi_name = (
                            TITHIS_SHUKLA[
                                curr_t_idx
                            ]
                        )

                    next_tithi_start_str = (
                        end_dt.strftime(
                            "%I:%M %p"
                        )
                    )

                    for sub_step in range(1, 60):

                        sub_jd = (
                            test_jd
                            + (sub_step * 0.5 / 24.0)
                        )

                        sub_s, _ = swe.calc_ut(
                            sub_jd,
                            swe.SUN,
                            flags
                        )

                        sub_m, _ = swe.calc_ut(
                            sub_jd,
                            swe.MOON,
                            flags
                        )

                        sub_diff = (
                            sub_m[0]
                            - sub_s[0]
                        ) % 360

                        if diff_deg >= 180.0:

                            sub_t_idx = (
                                int(
                                    (sub_diff - 180.0)
                                    // 12
                                ) % 15
                                if sub_diff >= 180.0
                                else
                                int(
                                    sub_diff // 12
                                ) % 15
                            )

                        else:

                            sub_t_idx = (
                                int(
                                    sub_diff // 12
                                ) % 15
                                if sub_diff < 180.0
                                else
                                int(
                                    (sub_diff - 180.0)
                                    // 12
                                ) % 15
                            )

                        if sub_t_idx != curr_t_idx:

                            sub_end_dt = (
                                datetime.fromtimestamp(
                                    (
                                        sub_jd
                                        + tz / 24.0
                                        - 2440587.5
                                    ) * 86400.0
                                )
                            )

                            next_tithi_end_str = (
                                sub_end_dt.strftime(
                                    "%I:%M %p"
                                )
                            )

                            break

                    break

        except Exception:
            pass

        moon_rashi_idx_start = int(
            moon_lon // 30
        ) % len(RASHIS)

        moon_transit_str = (
            f"{RASHIS[moon_rashi_idx_start]} राशि में स्थित"
        )

        try:

            for step in range(1, 96):

                test_jd = (
                    jd_sunrise
                    + (step * 0.25 / 24.0)
                )

                m_pos, _ = swe.calc_ut(
                    test_jd,
                    swe.MOON,
                    flags
                )

                m_r_idx = int(
                    m_pos[0] // 30
                ) % len(RASHIS)

                if m_r_idx != moon_rashi_idx_start:

                    transit_dt = (
                        datetime.fromtimestamp(
                            (
                                test_jd
                                + tz / 24.0
                                - 2440587.5
                            ) * 86400.0
                        )
                    )

                    moon_transit_str = (
                        f"{RASHIS[moon_rashi_idx_start]} "
                        f"से {RASHIS[m_r_idx]} में प्रवेश "
                        f"({transit_dt.strftime('%I:%M %p')})"
                    )

                    break

        except Exception:
            pass

        moon_nak_idx = int(
            moon_lon // (360.0 / 27.0)
        ) % len(NAKSHATRAS)

        nak_deg_rem = (
            moon_lon % (360.0 / 27.0)
        )

        pada_idx = int(
            nak_deg_rem // (360.0 / 108.0)
        ) % 4

        nak_lord = DASHA_LORDS[
            moon_nak_idx % 9
        ][0]

        yog_sum = (
            sun_lon + moon_lon
        ) % 360

        yog_idx = int(
            yog_sum // (360.0 / 27.0)
        ) % len(YOGS)

        karan_idx1 = int(
            diff_deg // 6
        ) % len(KARANS)

        karan_idx2 = (
            karan_idx1 + 1
        ) % len(KARANS)

        sun_rashi_idx = int(
            sun_lon // 30
        ) % len(RASHIS)

        moon_rashi_idx = int(
            moon_lon // 30
        ) % len(RASHIS)

        # Permanent Astronomical Purnimanta month calculation:
        maah_purnimant, purnimanta_idx = calculate_purnimanta_month(
            sun_lon,
            moon_lon,
            jd_sunrise
        )

        ritus = [
            "वसन्त ऋतु (चैत्र - वैशाख)",
            "ग्रीष्म ऋतु (ज्येष्ठ - आषाढ़)",
            "वर्षा ऋतु (श्रावण - भाद्रपद)",
            "शरद ऋतु (आश्विन - कार्तिक)",
            "हेमंत ऋतु (मार्गशीर्ष - पौष)",
            "शिशिर ऋतु (माघ - फाल्गुन)"
        ]

        current_ritu = ritus[
            (purnimanta_idx // 2)
            % len(ritus)
        ]

        vikram_samvat = (
            dt.year + 57
            if (
                dt.month > 4
                or (
                    dt.month == 4
                    and dt.day >= 13
                )
            )
            else dt.year + 56
        )

        shaka_samvat = (
            dt.year - 78
            if (
                dt.month > 3
                or (
                    dt.month == 3
                    and dt.day >= 22
                )
            )
            else dt.year - 79
        )

        kali_samvat = (
            dt.year + 3102
        )

        ayan_val = (
            "उत्तरायण"
            if (
                sun_rashi_idx >= 9
                or sun_rashi_idx <= 2
            )
            else "दक्षिणायन"
        )

        var_name = HINDI_DAYS[
            dt.weekday()
            % len(HINDI_DAYS)
        ]

        sunrise_dt = (
            datetime.fromtimestamp(
                (
                    jd_sunrise
                    + tz / 24.0
                    - 2440587.5
                ) * 86400.0
            )
        )

        sunrise_str = (
            sunrise_dt.strftime(
                "%I:%M %p"
            )
        )

        details_dict = {

            "tithi": tithi_name,

            "tithi_end_time": (
                tithi_end_str
                if tithi_end_str
                else "—"
            ),

            "paksha": paksha,

            "nakshatra": (
                NAKSHATRAS[moon_nak_idx]
            ),

            "nakshatra_pada": (
                f"चरण {pada_idx + 1}"
            ),

            "nakshatra_lord": nak_lord,

            "yog": YOGS[yog_idx],

            "karan_1": (
                KARANS[karan_idx1]
            ),

            "karan_2": (
                KARANS[karan_idx2]
            ),

            "var": var_name,

            "maah_purnimant": (
                maah_purnimant
            ),

            "chandra_rashi": (
                RASHIS[moon_rashi_idx]
            ),

            "moon_transit": (
                moon_transit_str
            ),

            "surya_rashi": (
                RASHIS[sun_rashi_idx]
            ),

            "ritu": current_ritu,

            "ayan": ayan_val,

            "vikram_samvat": str(
                vikram_samvat
            ),

            "shaka_samvat": str(
                shaka_samvat
            ),

            "kali_samvat": str(
                kali_samvat
            )
        }

        if next_tithi_name:

            details_dict[
                "next_tithi"
            ] = next_tithi_name

            details_dict[
                "next_tithi_start_time"
            ] = next_tithi_start_str

            if next_tithi_end_str:

                details_dict[
                    "next_tithi_end_time"
                ] = next_tithi_end_str

        return {

            "success": True,

            "data": {

                "location": {
                    "city": resolved_loc
                },

                "details": details_dict,

                "timings": {

                    "sunrise": sunrise_str,

                    "sunset": "07:10 PM",

                    "din_kaal": "13 घं 15 मि",

                    "ratri_kaal": "10 घं 45 मि",

                    "chandrodaya": "08:15 PM",

                    "chandrast": "07:28 AM"
                }
            }
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/full-panchang-hindi-fix")
def full_panchang_hindi_fix(
    date: str,
    city: str = "Ujjain"
):
    return full_panchang_hindi(
        date,
        city
    )
