import subprocess
import os
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

SWETEST_PATH = "/app/swetest"

# Correspondance symbole planète -> nom swetest
PLANETS = {
    "Su": 0,  # Sun
    "Mo": 1,  # Moon
    "Ma": 4,  # Mars
    "Me": 2,  # Mercury
    "Ju": 5,  # Jupiter
    "Ve": 3,  # Venus
    "Sa": 6,  # Saturn
    "Ra": 11, # Rahu (True Node)
    "Ke": None # Ketu = Rahu + 180
}

RASHI = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

RASHI_NUM = {name: i+1 for i, name in enumerate(RASHI)}

def deg_to_rashi(deg):
    deg = deg % 360
    rashi_index = int(deg // 30)
    degree_in_rashi = deg % 30
    return RASHI[rashi_index], round(degree_in_rashi, 4), rashi_index + 1

def run_swetest(date, time, lon, lat, planets_flag):
    cmd = [
        SWETEST_PATH,
        f"-b{date}",
        f"-ut{time}",
        f"-geopos{lon},{lat},0",
        f"-p{planets_flag}",
        "-fPl",
        "-eswe",
        "-roundsec",
        "-nohead"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout

def run_swetest_asc(date, time, lon, lat):
    cmd = [
        SWETEST_PATH,
        f"-b{date}",
        f"-ut{time}",
        f"-geopos{lon},{lat},0",
        "-p",
        "-hO",
        "-fPl",
        "-eswe",
        "-roundsec",
        "-nohead"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout

def parse_planet_output(output):
    planets_data = {}
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Format : "Sun        355°6'43"  Pisces"
        match = re.match(r"(\w+)\s+([\d]+)°([\d]+)'([\d]+)\"\s+(\w+)", line)
        if match:
            name = match.group(1)
            deg = int(match.group(2)) + int(match.group(3))/60 + int(match.group(4))/3600
            sign = match.group(5)
            planets_data[name] = {"deg": round(deg, 4), "sign": sign, "rashi_num": RASHI_NUM.get(sign, 0)}
    return planets_data

@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    date = data.get("date", "2000.01.01")       # format: YYYY.MM.DD
    time = data.get("time", "12:00:00")          # format: HH:MM:SS
    lat  = str(data.get("lat", 48.8566))
    lon  = str(data.get("lon", 2.3522))

    try:
        # Planètes principales : 0123456 + 11 (Rahu)
        raw = run_swetest(date, time, lon, lat, "01234567")
        parsed = parse_planet_output(raw)

        # Construire graha
        name_map = {
            "Sun": "Su", "Moon": "Mo", "Mercury": "Me",
            "Venus": "Ve", "Mars": "Ma", "Jupiter": "Ju",
            "Saturn": "Sa"
        }

        graha = {}
        for swetest_name, symbol in name_map.items():
            if swetest_name in parsed:
                p = parsed[swetest_name]
                rashi, deg_in_rashi, rashi_num = deg_to_rashi(p["deg"])
                graha[symbol] = {
                    "name": swetest_name,
                    "lon": p["deg"],
                    "rashi": rashi,
                    "rashi_num": rashi_num,
                    "deg_in_rashi": deg_in_rashi
                }

        # Rahu (node 11)
        raw_rahu = run_swetest(date, time, lon, lat, "11")
        parsed_rahu = parse_planet_output(raw_rahu)
        if "true Node" in parsed_rahu or "TrueNode" in parsed_rahu or "Mean Node" in parsed_rahu:
            rahu_key = next(iter(parsed_rahu))
            rahu_deg = parsed_rahu[rahu_key]["deg"]
        else:
            rahu_deg = 0.0

        rahu_rashi, rahu_deg_in, rahu_rashi_num = deg_to_rashi(rahu_deg)
        graha["Ra"] = {
            "name": "Rahu",
            "lon": rahu_deg,
            "rashi": rahu_rashi,
            "rashi_num": rahu_rashi_num,
            "deg_in_rashi": rahu_deg_in
        }

        # Ketu = Rahu + 180
        ketu_deg = (rahu_deg + 180) % 360
        ketu_rashi, ketu_deg_in, ketu_rashi_num = deg_to_rashi(ketu_deg)
        graha["Ke"] = {
            "name": "Ketu",
            "lon": ketu_deg,
            "rashi": ketu_rashi,
            "rashi_num": ketu_rashi_num,
            "deg_in_rashi": ketu_deg_in
        }

        # Ascendant
        raw_asc = run_swetest_asc(date, time, lon, lat)
        asc_deg = 0.0
        for line in raw_asc.strip().split("\n"):
            if "Ascendant" in line or "asc" in line.lower():
                m = re.search(r"([\d]+)°([\d]+)'([\d]+)\"", line)
                if m:
                    asc_deg = int(m.group(1)) + int(m.group(2))/60 + int(m.group(3))/3600

        asc_rashi, asc_deg_in, asc_rashi_num = deg_to_rashi(asc_deg)
        lagna = {
            "lon": asc_deg,
            "rashi": asc_rashi,
            "rashi_num": asc_rashi_num,
            "deg_in_rashi": asc_deg_in
        }

        # Panchanga basique
        sun_lon = graha.get("Su", {}).get("lon", 0)
        moon_lon = graha.get("Mo", {}).get("lon", 0)
        tithi_num = int(((moon_lon - sun_lon) % 360) / 12) + 1
        nakshatra_num = int((moon_lon % 360) / (360/27)) + 1

        panchanga = {
            "tithi": tithi_num,
            "nakshatra": nakshatra_num
        }

        return jsonify({
            "chart": {
                "graha": graha,
                "lagna": lagna,
                "panchanga": panchanga
            }
        })

    except FileNotFoundError:
        return jsonify({"error": f"swetest not found at {SWETEST_PATH}"}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "swetest timeout"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    exists = os.path.isfile(SWETEST_PATH) and os.access(SWETEST_PATH, os.X_OK)
    return jsonify({"swetest": "ok" if exists else "missing"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9393)
