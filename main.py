from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
import datetime
import pytz
import ephem
import math

app = Flask(__name__)
CORS(app) 

# --- ज्योतिषीय डेटा (Hindi Data) ---
RASHI_NAMES = ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]
NAKSHATRA_NAMES = ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "आश्लेषा", 
                   "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाति", "विशाखा", "अनुराधा", 
                   "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती"]
TITHI_NAMES = ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
               "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावस्या"]
YOGA_NAMES = ["विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि", "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात", "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म", "ऐन्द्र", "वैधृति"]
KARANA_NAMES = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि", "शकुनि", "चतुष्पाद", "नाग", "किस्तुघ्न"]
DAYS_HINDI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
HINDI_MONTHS = ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"]

def get_julian_day(dt):
    utc_dt = dt.astimezone(pytz.utc)
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)

# ==========================================
# 1. PANCHANG API
# ==========================================
@app.route('/api/full-panchang-hindi-fix', methods=['GET'])
@app.route('/api/full-panchang-hindi', methods=['GET'])
def get_panchang():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"success": False, "error": "Date is required"}), 400

    try:
        y, m, d = map(int, date_str.split('-'))
        local_tz = pytz.timezone('Asia/Kolkata')
        
        dt = local_tz.localize(datetime.datetime(y, m, d, 12, 0))
        jd = get_julian_day(dt)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        sun_pos, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        sun_lon, sun_speed = sun_pos[0], sun_pos[3]
        moon_lon, moon_speed = moon_pos[0], moon_pos[3]

        angle_diff = (moon_lon - sun_lon) % 360
        tithi_val = angle_diff / 12.0
        tithi_idx = int(tithi_val)
        tithi_name = TITHI_NAMES[tithi_idx]
        paksha = "शुक्ल पक्ष" if tithi_idx < 15 else "कृष्ण पक्ष"
        
        rel_speed = moon_speed - sun_speed
        deg_left = ((tithi_idx + 1) * 12) - angle_diff
        time_left_jd = deg_left / rel_speed
        end_jd = jd + time_left_jd
        
        y_e, m_e, d_e, h_e = swe.revjul(end_jd, swe.GREG_CAL)
        end_dt_utc = datetime.datetime(y_e, m_e, d_e) + datetime.timedelta(hours=h_e)
        end_dt_utc = pytz.utc.localize(end_dt_utc)
        end_dt_local = end_dt_utc.astimezone(local_tz)
        
        if end_dt_local.date() > dt.date():
            tithi_end_time = end_dt_local.strftime("अगले दिन %I:%M %p")
        else:
            tithi_end_time = end_dt_local.strftime("%I:%M %p")

        nak_idx = int(moon_lon / (360/27.0))
        nak_name = NAKSHATRA_NAMES[nak_idx]
        yog_idx = int((sun_lon + moon_lon) % 360 / (360/27.0))
        yog_name = YOGA_NAMES[yog_idx]

        karan_val = (moon_lon - sun_lon) % 360 / 6.0
        karan_idx = int(karan_val)
        def get_karan_name(k_idx):
            if k_idx == 0: return "किस्तुघ्न"
            elif k_idx == 57: return "शकुनि"
            elif k_idx == 58: return "चतुष्पाद"
            elif k_idx == 59: return "नाग"
            else: return KARANA_NAMES[(k_idx - 1) % 7]
            
        karan_1 = get_karan_name(karan_idx)
        karan_2 = get_karan_name((karan_idx + 1) % 60)

        var_name = DAYS_HINDI[dt.weekday()]
        surya_rashi_idx = int(sun_lon / 30)
        chandra_rashi = RASHI_NAMES[int(moon_lon / 30)]
        surya_rashi = RASHI_NAMES[surya_rashi_idx]
        vikram_samvat = str(y + 57)

        ayan = "उत्तरायण" if surya_rashi_idx in [9, 10, 11, 0, 1, 2] else "दक्षिणायन"
        ritu_map = {11:"वसंत", 0:"वसंत", 1:"ग्रीष्म", 2:"ग्रीष्म", 3:"वर्षा", 4:"वर्षा", 5:"शरद", 6:"शरद", 7:"हेमंत", 8:"हेमंत", 9:"शिशिर", 10:"शिशिर"}
        ritu = ritu_map.get(surya_rashi_idx, "--")

        sun_lon_at_amavasya = (sun_lon - (angle_diff * 0.0808)) % 360
        amavasya_rashi_idx = int(sun_lon_at_amavasya / 30)
        amanta_idx = (amavasya_rashi_idx + 1) % 12
        purnimant_idx = (amanta_idx + 1) % 12 if tithi_idx >= 15 else amanta_idx
        maah_purnimant = HINDI_MONTHS[purnimant_idx]

        observer = ephem.Observer()
        observer.lat, observer.lon = '23.1765', '75.7885' 
        
        start_of_day = local_tz.localize(datetime.datetime(y, m, d, 0, 5)).astimezone(pytz.utc)
        observer.date = start_of_day
        sun = ephem.Sun()
        try:
            sun_rise_utc = observer.next_rising(sun).datetime()
            sunrise = pytz.utc.localize(sun_rise_utc).astimezone(local_tz).strftime("%I:%M %p")
        except:
            sunrise = "--"

        return jsonify({
            "success": True,
            "data": {
                "details": {
                    "tithi": tithi_name,
                    "tithi_end_time": tithi_end_time,
                    "paksha": paksha,
                    "nakshatra": nak_name,
                    "yog": yog_name,
                    "karan_1": karan_1,
                    "karan_2": karan_2,
                    "var": var_name,
                    "chandra_rashi": chandra_rashi,
                    "surya_rashi": surya_rashi,
                    "vikram_samvat": vikram_samvat,
                    "ayan": ayan,
                    "ritu": ritu,
                    "maah_purnimant": maah_purnimant
                },
                "timings": {
                    "sunrise": sunrise
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# 2. KUNDALI API (ADDED EXACT lon_decimal)
# ==========================================
@app.route('/api/generate-kundali', methods=['GET', 'POST'])
def generate_kundali():
    if request.method == 'POST':
        data = request.json or {}
        date_str = data.get('dob') or data.get('date')
        time_str = data.get('time')
    else:
        date_str = request.args.get('date')
        time_str = request.args.get('time')
        
    if not date_str or not time_str:
        return jsonify({"success": False, "error": "Date and Time are required"}), 400

    try:
        y, m, d = map(int, date_str.split('-'))
        hh, mm = map(int, time_str.split(':'))
        
        local_tz = pytz.timezone('Asia/Kolkata')
        dt = local_tz.localize(datetime.datetime(y, m, d, hh, mm))
        jd = get_julian_day(dt)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        planets_to_calc = {
            "सूर्य": swe.SUN, "चंद्र": swe.MOON, "मंगल": swe.MARS, 
            "बुध": swe.MERCURY, "गुरु": swe.JUPITER, "शुक्र": swe.VENUS, 
            "शनि": swe.SATURN, "राहु": swe.MEAN_NODE
        }
        
        planet_data = {}
        sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]

        for name, p_id in planets_to_calc.items():
            pos, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            lon_deg = pos[0]
            speed = pos[3]
            
            is_asta = False
            if name not in ["सूर्य", "चंद्र", "राहु"]:
                diff = abs(lon_deg - sun_lon)
                if diff > 180: diff = 360 - diff
                if diff <= 8.5: is_asta = True

            # ✨ NEW: Added 'lon_decimal' for 100% exact frontend calculations
            planet_data[name] = {
                "rashi": RASHI_NAMES[int(lon_deg / 30)],
                "rashi_num": int(lon_deg / 30) + 1,
                "degree": f"{int(lon_deg % 30)}°{int(((lon_deg % 30) % 1) * 60)}'",
                "lon_decimal": float(lon_deg), 
                "is_vakri": bool(speed < 0),
                "is_asta": is_asta
            }
            
        ketu_lon = (swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] + 180) % 360
        planet_data["केतु"] = {
            "rashi": RASHI_NAMES[int(ketu_lon / 30)],
            "rashi_num": int(ketu_lon / 30) + 1,
            "degree": f"{int(ketu_lon % 30)}°{int(((ketu_lon % 30) % 1) * 60)}'",
            "lon_decimal": float(ketu_lon),
            "is_vakri": True,
            "is_asta": False
        }
        
        lat, lon = 23.1765, 75.7885
        houses, ascmc = swe.houses(jd, lat, lon, b'P')
        lagna_sidereal = (ascmc[0] - swe.get_ayanamsa_ut(jd)) % 360
        lagna_rashi_num = int(lagna_sidereal / 30)

        return jsonify({
            "success": True,
            "lagna": {
                "rashi": RASHI_NAMES[lagna_rashi_num],
                "rashi_num": lagna_rashi_num + 1,
                "degree": f"{int(lagna_sidereal % 30)}°{int(((lagna_sidereal % 30) % 1) * 60)}'",
                "lon_decimal": float(lagna_sidereal)
            },
            "planets": planet_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
