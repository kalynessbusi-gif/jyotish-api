from flask import Flask, jsonify, request
import swisseph as swe

app = Flask(__name__)

# -----------------------------
# ROUTE TEST
# -----------------------------
@app.route("/")
def home():
    return "Jyotish API running"


@app.route("/api/ping")
def ping():
    return jsonify({"pong": "success"})


# -----------------------------
# CALCUL ASTROLOGIQUE
# -----------------------------
@app.route("/api/calculate")
def calculate():

    try:
        # récupérer paramètres
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))
        day = int(request.args.get("day"))
        hour = float(request.args.get("hour"))

        # conversion date → Julian Day
        jd = swe.julday(year, month, day, hour)

        # planètes principales
        planets = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
        }

        results = {}

        # calcul positions
        for name, planet in planets.items():
            pos = swe.calc_ut(jd, planet)[0][0]
            results[name] = round(pos, 2)

        return jsonify({
            "status": "success",
            "julian_day": jd,
            "planets": results
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


# -----------------------------
# LANCEMENT LOCAL
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9393)
