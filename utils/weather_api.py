import requests

def fetch_weather(lat, lon):
    """Fetch current weather from Open-Meteo (free, no API key needed)."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_max"
            f"&timezone=auto&forecast_days=7"
        )
        resp = requests.get(url, timeout=10)
        data = resp.json()

        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        temp = current.get("temperature", 28)
        
        # Average over 7 days
        humidity_vals = daily.get("relative_humidity_2m_max", [75])
        humidity = sum(humidity_vals) / len(humidity_vals) if humidity_vals else 75

        precip_vals = daily.get("precipitation_sum", [0])
        # Annualize: weekly avg * 52
        weekly_rain = sum(precip_vals)
        rainfall = weekly_rain * 52 / 7  # rough annual estimate

        return {
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "rainfall": round(rainfall, 1),
            "source": "Open-Meteo API"
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return {
            "temperature": 28.0,
            "humidity": 75.0,
            "rainfall": 800.0,
            "source": "Default (API failed)"
        }
