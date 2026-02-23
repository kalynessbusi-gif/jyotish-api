import subprocess
import os
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

SWETEST_PATH = "/app/swetest"

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

def run_swetest_houses(date, time, lon, lat):
    cmd = [
        SWETEST_PATH,
        f"-b{date}",
        f"-ut{time}",
        f"-geopos{lon},{lat},0",
        f"-house{lon},{lat},P",
        "-fPl",
        "-eswe",
        "-roundsec",
        "-nohead"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout

def parse_ascendant(output):
    for line in output.strip().split("\n"):
        if line.strip().startswith("Ascendant"):
            match = re.search(r"([\d]+\.[\d]+)", line)
            if match:
                return float(match.group(1))
    return 0.0

def parse_planet_output(output):
    planets_data = {}
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line or "warning" in line.lower() or "error" in line.lower():
            continue
        match = re.match(r"([A-Za-z][A-Za-z _]+?)\s{2,}([\d]+\.[\d]+)", line)
        if not match:
            match = re.match(r"([A-Za-z]+)\s+([\d]+\.[\d]+)", line)
        if match:
            name = match.group(1).strip()
            deg = float(match.group(2))
            rashi, deg_in_rashi, rashi_num = deg_to_rashi(deg)
            planets_data[name] = {
                "deg": round(deg, 6),
                "sign": rashi,
                "rashi_num": rashi_num,
                "deg_in_rashi": deg_in_rashi
            }
    return planets_data

@app.route("/debug", methods=["GET"])
def debug():
    date = request.args.get("date", "1997.03.15")
    time = request.args.get("time", "15:00:00")
    lat = "48.8566"
    lon = "2.3522"

    raw = run_swetest(date, time, lon, lat, "0123456")
    raw_rahu = run_swetest(date, time, lon, lat, "m")
    raw_asc = run_swetest_houses(date, time, lon, lat)

    return jsonify({
        "planets_parsed": parse_planet_output(raw),
        "rahu_parsed": parse_planet_output(raw_rahu),
        "ascendant_deg": parse_ascendant(raw_asc),
    })

@app.route("/api/calculate", methods=["GET", "POST"])
def calculate():
    if request.method == "POST":
        data = request.get_json() or {}
    else:
        data = request.args

    year  = str(data.get("year", "2000"))
    month = str(data.get("month", "01")).zfill(2)
    day   = str(data.get("day", "01")).zfill(2)
    hour  = str(data.get("hour", "12")).zfill(2)

    date = f"{year}.{month}.{day}"
    time = f"{hour}:00:00"

    # Accepte latitude OU lat, longitude OU lon
    lat = str(data.get("latitude") or data.get("lat") or "48.8566")
    lon = str(data.get("longitude") or data.get("lon") or "2.3522")

    try:
        raw = run_swetest(date, time, lon, lat, "0123456")
        parsed = parse_planet_output(raw)

        name_map = {
            "Sun": "Su", "Moon": "Mo", "Mercury": "Me",
            "Venus": "Ve", "Mars": "Ma", "Jupiter": "Ju",
            "Saturn": "Sa"
        }

        graha = {}
        for swetest_name, symbol in name_map.items():
            if swetest_name in parsed:
                p = parsed[swetest_name]
                graha[symbol] = {
                    "name": swetest_name,
                    "lon": p["deg"],
                    "rashi": p["sign"],
                    "rashi_num": p["rashi_num"],
                    "deg_in_rashi": p["deg_in_rashi"]
                }

        # Rahu = mean node
        raw_rahu = run_swetest(date, time, lon, lat, "m")
        parsed_rahu = parse_planet_output(raw_rahu)
        rahu_deg = 0.0
        for key, val in parsed_rahu.items():
            if "node" in key.lower() or "mean" in key.lower():
                rahu_deg = val["deg"]
                break
        if rahu_deg == 0.0 and parsed_rahu:
            rahu_deg = next(iter(parsed_rahu.values()))["deg"]

        rahu_rashi, rahu_deg_in, rahu_rashi_num = deg_to_rashi(rahu_deg)
        graha["Ra"] = {
            "name": "Rahu",
            "lon": rahu_deg,
            "rashi": rahu_rashi,
            "rashi_num": rahu_rashi_num,
            "deg_in_rashi": rahu_deg_in
        }

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
        raw_asc = run_swetest_houses(date, time, lon, lat)
        asc_deg = parse_ascendant(raw_asc)

        asc_rashi, asc_deg_in, asc_rashi_num = deg_to_rashi(asc_deg)
        lagna = {
            "lon": asc_deg,
            "rashi": asc_rashi,
            "rashi_num": asc_rashi_num,
            "deg_in_rashi": asc_deg_in
        }

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
```

Push Railway, puis teste directement avec les vrais paramètres du frontend :
```
https://jyotish-api-production-a50f.up.railway.app/api/calculate?year=1997&month=3&day=15&hour=15&latitude=48.8566&longitude=2.3522
