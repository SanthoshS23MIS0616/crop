from flask import Flask, render_template, request, jsonify
from utils.crop_engine import CropEngine
from utils.weather_api import fetch_weather

app = Flask(__name__)
engine = CropEngine("data/crop_data.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_weather", methods=["POST"])
def get_weather():
    data = request.json
    lat = float(data.get("lat", 13.08))
    lon = float(data.get("lon", 80.27))
    weather = fetch_weather(lat, lon)
    return jsonify(weather)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    n = float(data["n"])
    p = float(data["p"])
    k = float(data["k"])
    ph = float(data["ph"])
    temp = float(data["temp"])
    humidity = float(data["humidity"])
    rainfall = float(data["rainfall"])
    area = float(data["area"])
    lat = data.get("lat", "N/A")
    lon = data.get("lon", "N/A")

    result = engine.predict(n, p, k, ph, temp, humidity, rainfall, area)
    result["location"] = {"lat": lat, "lon": lon}
    return jsonify(result)

# Only run this locally for development
# Render uses gunicorn — do NOT run app.run() in production
if __name__ == "__main__":
    import os
    if os.getenv("FLASK_ENV") == "development":
        app.run(debug=True, host="0.0.0.0", port=5000)