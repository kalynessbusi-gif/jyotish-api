from flask import Flask, jsonify, request
import subprocess
import json

app = Flask(__name__)

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

    try:
        # appel swetest (Swiss Ephemeris)
        cmd = [
            "./swetest",
            "-b{}-{}-{}".format(day, month, year),
            "-ut{}:{}".format(hour, minute),
            "-p0123456789",
            "-eswe",
            "-fPlZ",
            "-g,",
        ]

        result = subprocess.check_output(cmd).decode()

        return jsonify({
            "status": "success",
            "raw_output": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9393)
