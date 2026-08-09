from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
import datetime
import pytz

app = Flask(__name__)
# AppCreator24 के HTML व्यू से API कॉल करने के लिए CORS ज़रूरी है
CORS(app) 

# 12 राशियां और 27 नक्षत्र
RASHI_NAMES = ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]
NAKSHATRA_NAMES = ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "आश्लेषा", 
                   "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाति", "विशाखा", "अनुराधा", 
                   "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती"]

def get_kundali_data(year, month, day, hour, minute, lat, lon):
    # 1. भारतीय समय (IST) को UTC में बदलना
    local_tz = pytz.timezone('Asia/Kolkata')
    dt = datetime.datetime(year, month, day, hour, minute)
    local_dt = local_tz.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    
    # जूलियन डे (Julian Day) निकालना
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60.0)
    
    # 2. लाहिरी अयनांश सेट करना (भारतीय वैदिक ज्योतिष)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # 3. ग्रहों की लिस्ट
    planets = {
        "सूर्य": swe.SUN,
        "चंद्र": swe.MOON,
        "मंगल": swe.MARS,
        "बुध": swe.MERCURY,
        "गुरु": swe.JUPITER,
        "शुक्र": swe.VENUS,
        "शनि": swe.SATURN,
        "राहु": swe.MEAN_NODE
    }
    
    planet_details = {}
    
    # 4. हर ग्रह की स्थिति और गति निकालना
    for name, p_id in planets.items():
        pos, ret = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        lon_deg = pos[0]
        speed = pos[3] # गति (- में है तो वक्री)
        
        rashi_index = int(lon_deg / 30)
        nak_index = int(lon_deg / (360/27))
        degree_in_rashi = lon_deg % 30
        
        is_vakri = True if speed < 0 else False
        
        planet_details[name] = {
            "rashi": RASHI_NAMES[rashi_index],
            "rashi_num": rashi_index + 1,
            "degree": f"{int(degree_in_rashi)}°{int((degree_in_rashi % 1) * 60)}'",
            "nakshatra": NAKSHATRA_NAMES[nak_index],
            "is_vakri": is_vakri
        }
        
    # राहु से केतु की स्थिति (180 डिग्री सामने)
    ketu_lon = (swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] + 180) % 360
    ketu_rashi = int(ketu_lon / 30)
    ketu_nak = int(ketu_lon / (360/27))
    planet_details["केतु"] = {
        "rashi": RASHI_NAMES[ketu_rashi],
        "rashi_num": ketu_rashi + 1,
        "degree": f"{int(ketu_lon % 30)}°{int((ketu_lon % 1) * 60)}'",
        "nakshatra": NAKSHATRA_NAMES[ketu_nak],
        "is_vakri": True
    }
    
    # 5. लग्न (Ascendant / 1st House) निकालना
    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    lagna_lon = ascmc[0]
    ayanamsa = swe.get_ayanamsa_ut(jd)
    lagna_sidereal = (lagna_lon - ayanamsa) % 360
    lagna_rashi = int(lagna_sidereal / 30)
    
    return {
        "success": True,
        "lagna": {
            "rashi": RASHI_NAMES[lagna_rashi],
            "rashi_num": lagna_rashi + 1,
            "degree": f"{int(lagna_sidereal % 30)}°",
        },
        "planets": planet_details
    }

# API Route
@app.route('/api/generate-kundali', methods=['GET'])
def generate_kundali_api():
    date_str = request.args.get('date') # Format: YYYY-MM-DD
    time_str = request.args.get('time') # Format: HH:MM
    
    # अगर यूज़र ने लोकेशन नहीं डाली, तो डिफ़ॉल्ट उज्जैन लें
    # (बाद में हम इसे डायनामिक करेंगे)
    lat = float(request.args.get('lat', 23.1765))
    lon = float(request.args.get('lon', 75.7885))
    
    if not date_str or not time_str:
        return jsonify({"success": False, "error": "तारीख और समय देना आवश्यक है (date, time)"}), 400
        
    try:
        y, m, d = map(int, date_str.split('-'))
        hh, mm = map(int, time_str.split(':'))
        
        kundali_data = get_kundali_data(y, m, d, hh, mm, lat, lon)
        return jsonify(kundali_data)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# होम पेज टेस्ट के लिए
@app.route('/')
def home():
    return "Kundali API is running! Use /api/generate-kundali"

if __name__ == '__main__':
    # Render पर 0.0.0.0 और पोर्ट ज़रूरी है
    app.run(host='0.0.0.0', port=5000)
