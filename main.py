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

@app.route('/api/full-panchang-hindi-fix', methods=['GET'])
@app.route('/api/full-panchang-hindi', methods=['GET'])
def get_panchang():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"success": False, "error": "Date is required"}), 400

    try:
        y, m, d = map(int, date_str.split('-'))
        local_tz = pytz.timezone('Asia/Kolkata')
        
        # दोपहर 12 बजे का पंचांग आधार
        dt = local_tz.localize(datetime.datetime(y, m, d, 12, 0))
        jd = get_julian_day(dt)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # सूर्य और चंद्र की स्थिति एवं गति (Speed)
        sun_pos, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        sun_lon, sun_speed = sun_pos[0], sun_pos[3]
        moon_lon, moon_speed = moon_pos[0], moon_pos[3]

        # 1. तिथि, पक्ष और तिथि समाप्ति समय (Tithi End Time)
        angle_diff = (moon_lon - sun_lon) % 360
        tithi_val = angle_diff / 12.0
        tithi_idx = int(tithi_val)
        tithi_name = TITHI_NAMES[tithi_idx]
        paksha = "शुक्ल पक्ष" if tithi_idx < 15 else "कृष्ण पक्ष"
        
        # समाप्ति समय का सटीक गणित
        rel_speed = moon_speed - sun_speed
        deg_left = ((tithi_idx + 1) * 12) - angle_diff
        time_left_jd = deg_left / rel_speed
        end_jd = jd + time_left_jd
        
        y_e, m_e, d_e, h_e = swe.revjul(end_jd, swe.GREG_CAL)
        end_dt_utc = datetime.datetime(y_e, m_e, d_e) + datetime.timedelta(hours=h_e)
        end_dt_utc = pytz.utc.localize(end_dt_utc)
        end_dt_local = end_dt_utc.astimezone(local_tz)
        
        # अगर तिथि अगले दिन समाप्त हो रही है
        if end_dt_local.date() > dt.date():
            tithi_end_time = end_dt_local.strftime("अगले दिन %I:%M %p")
        else:
            tithi_end_time = end_dt_local.strftime("%I:%M %p")

        # 2. नक्षत्र
        nak_idx = int(moon_lon / (360/27.0))
        nak_name = NAKSHATRA_NAMES[nak_idx]

        # 3. योग
        yog_idx = int((sun_lon + moon_lon) % 360 / (360/27.0))
        yog_name = YOGA_NAMES[yog_idx]

        # 4. करण
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

        # 5. वार, राशि, संवत
        var_name = DAYS_HINDI[dt.weekday()]
        surya_rashi_idx = int(sun_lon / 30)
        chandra_rashi = RASHI_NAMES[int(moon_lon / 30)]
        surya_rashi = RASHI_NAMES[surya_rashi_idx]
        vikram_samvat = str(y + 57)
        shaka_samvat = str(y - 78)
        kali_samvat = str(y + 3101)

        # 6. अयन और ऋतु
        ayan = "उत्तरायण" if surya_rashi_idx in [9, 10, 11, 0, 1, 2] else "दक्षिणायन"
        ritu_map = {11:"वसंत", 0:"वसंत", 1:"ग्रीष्म", 2:"ग्रीष्म", 3:"वर्षा", 4:"वर्षा", 5:"शरद", 6:"शरद", 7:"हेमंत", 8:"हेमंत", 9:"शिशिर", 10:"शिशिर"}
        ritu = ritu_map.get(surya_rashi_idx, "--")

        # 7. माह (पूर्णिमांत)
        sun_lon_at_amavasya = (sun_lon - (angle_diff * 0.0808)) % 360
        amavasya_rashi_idx = int(sun_lon_at_amavasya / 30)
        amanta_idx = (amavasya_rashi_idx + 1) % 12
        purnimant_idx = (amanta_idx + 1) % 12 if tithi_idx >= 15 else amanta_idx
        maah_purnimant = HINDI_MONTHS[purnimant_idx]

        # 8. Ephem से सूर्योदय/सूर्यास्त
        observer = ephem.Observer()
        observer.lat, observer.lon = '23.1765', '75.7885' 
        observer.date = dt.astimezone(pytz.utc)
        
        sun = ephem.Sun()
        try:
            sunrise = ephem.localtime(observer.previous_rising(sun)).strftime("%I:%M %p")
            sunset = ephem.localtime(observer.next_setting(sun)).strftime("%I:%M %p")
        except:
            sunrise, sunset = "--", "--"
        
        moon = ephem.Moon()
        try: chandrodaya = ephem.localtime(observer.previous_rising(moon)).strftime("%I:%M %p")
        except: chandrodaya = "--"
        try: chandrast = ephem.localtime(observer.next_setting(moon)).strftime("%I:%M %p")
        except: chandrast = "--"

        return jsonify({
            "success": True,
            "data": {
                "location": request.args.get('city', 'Ujjain'),
                "summary_header": f"{tithi_name}, {nak_name} नक्षत्र",
                "details": {
                    "tithi": tithi_name,
                    "tithi_end_time": tithi_end_time,  # <--- नया डेटा जुड़ गया
                    "paksha": paksha,
                    "nakshatra": nak_name,
                    "yog": yog_name,
                    "karan_1": karan_1,
                    "karan_2": karan_2,
                    "var": var_name,
                    "chandra_rashi": chandra_rashi,
                    "surya_rashi": surya_rashi,
                    "vikram_samvat": vikram_samvat,
                    "shaka_samvat": shaka_samvat,
                    "kali_samvat": kali_samvat,
                    "ayan": ayan,
                    "ritu": ritu,
                    "maah_purnimant": maah_purnimant
                },
                "timings": {
                    "sunrise": sunrise,
                    "sunset": sunset,
                    "din_kaal": "लगभग 12 घंटे",
                    "ratri_kaal": "लगभग 12 घंटे",
                    "chandrodaya": chandrodaya,
                    "chandrast": chandrast
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate-kundali', methods=['GET', 'POST'])
def generate_kundali():
    # ... (आपका मौजूदा कुण्डली वाला कोड यहाँ रहेगा, उसमें कोई बदलाव नहीं है) ...
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
