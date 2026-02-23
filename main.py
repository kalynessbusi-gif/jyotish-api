from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Jyotish API running"

@app.route("/api/ping")
def ping():
    return jsonify({"pong": "success"})

@app.route("/api/calculate")
def calculate():
    # placeholder (Lovable test)
    data = request.args.to_dict()
    return jsonify({
        "status": "ok",
        "received": data
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9393)
