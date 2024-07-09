from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


@app.route("/api/hello")
def hello():
    visitor_name = request.args.get("visitor_name", "Guest")
    client_ip = request.environ.get("HTTP_X_REAL_IP", request.remote_addr)
    try:
        # Use ipapi.co to get location info
        geo_response = requests.get(f"https://ipapi.co/{client_ip}/json/", timeout=10)
        geo_data = geo_response.json()

        city = geo_data.get("city", "Unknown")
        latitude = geo_data.get("latitude", "Unknown")
        longitude = geo_data.get("longitude", "Unknown")

        # Fetch weather data
        weather_response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m&forecast_days=1",
            timeout=10,
        )
        weather_data = weather_response.json()
        temperature = weather_data["current"]["temperature_2m"]

        response = {
            "client_ip": client_ip,
            "location": city,
            "greeting": f"Hello, {visitor_name}! The temperature is {temperature} degrees Celsius in {city}",
        }

        return jsonify(response)
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to fetch data from external api"}), 500


if __name__ == "__main__":
    app.run(port=3000)
