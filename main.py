from flask import Flask, jsonify, request
import subprocess
import os

app = Flask(__name__)

# ---------------------------------------------------
# Trouver automatiquement swetest dans Railway
# ---------------------------------------------------
def get_swetest_path():
    possible_paths = [
        "/app/swetest",
        "./swetest",
        os.path.join(os.getcwd(), "swetest")
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


@app.route("/")
def home():
    return "Jyotish API running"


@app.route("/api/ping")
def ping():
    return jsonify({"pong": "success"})


@app.route("/api/calculate")
def calculate():

    lat = request.args.get("latitude")
    lon = request.args.get("longitude")
    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")
    hour = request.args.get("hour")
    minute = request.args.get("min")
    tz = request.args.get("time_zone")

    swetest_path = get_swetest_path()

    # 🔴 sécurité : vérifier que swetest existe
    if not swetest_path:
        return jsonify({
            "status": "error",
            "message": "swetest binary not found in container"
        }), 500

    try:
        cmd = [
            swetest_path,
            f"-b{day}-{month}-{year}",
            f"-ut{hour}:{minute}",
            "-p0123456789",
            "-eswe",
            "-fPlZ",
            "-g,",
        ]

        result = subprocess.check_output(cmd).decode()

        return jsonify({
            "status": "success",
            "swetest_path": swetest_path,
            "raw_output": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9393)
