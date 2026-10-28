import sys, os, requests
from datetime import date, timedelta
from bson import ObjectId

# lets this script import db.py from the project folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import locations, create_indexes

# name, country, region, latitude, longitude, elevation (m), tags
CITIES = [
    ("Belfast", "UK", "Northern Ireland", 54.5973, -5.9301, 10, ["coastal", "city"]),
    ("London", "UK", "England", 51.5074, -0.1278, 11, ["city"]),
    ("Edinburgh", "UK", "Scotland", 55.9533, -3.1883, 47, ["coastal", "city"]),
    ("Cardiff", "UK", "Wales", 51.4816, -3.1791, 11, ["coastal", "city"]),
    ("Manchester", "UK", "England", 53.4808, -2.2426, 38, ["city"]),
    ("Dublin", "Ireland", "Leinster", 53.3498, -6.2603, 20, ["coastal", "city"]),
    ("Paris", "France", "Ile-de-France", 48.8566, 2.3522, 35, ["city"]),
    ("Madrid", "Spain", "Madrid", 40.4168, -3.7038, 667, ["inland", "hot"]),
    ("Lisbon", "Portugal", "Lisboa", 38.7223, -9.1393, 2, ["coastal", "hot"]),
    ("Rome", "Italy", "Lazio", 41.9028, 12.4964, 21, ["city", "hot"]),
    ("Berlin", "Germany", "Berlin", 52.5200, 13.4050, 34, ["city", "inland"]),
    ("Amsterdam", "Netherlands", "North Holland", 52.3676, 4.9041, 0, ["coastal", "city"]),
    ("Oslo", "Norway", "Oslo", 59.9139, 10.7522, 23, ["coastal", "cold"]),
    ("Reykjavik", "Iceland", "Capital Region", 64.1466, -21.9426, 14, ["coastal", "cold"]),
    ("Athens", "Greece", "Attica", 37.9838, 23.7275, 70, ["city", "hot"]),
    ("Istanbul", "Turkey", "Marmara", 41.0082, 28.9784, 40, ["coastal", "city"]),
    ("Moscow", "Russia", "Moscow", 55.7558, 37.6173, 156, ["inland", "cold"]),
    ("Cairo", "Egypt", "Cairo", 30.0444, 31.2357, 23, ["desert", "hot"]),
    ("Lagos", "Nigeria", "Lagos", 6.5244, 3.3792, 41, ["coastal", "hot"]),
    ("Nairobi", "Kenya", "Nairobi", -1.2921, 36.8219, 1795, ["inland", "mountain"]),
    ("Cape Town", "South Africa", "Western Cape", -33.9249, 18.4241, 25, ["coastal"]),
    ("Dubai", "UAE", "Dubai", 25.2048, 55.2708, 5, ["desert", "hot", "coastal"]),
    ("Mumbai", "India", "Maharashtra", 19.0760, 72.8777, 14, ["coastal", "hot"]),
    ("Delhi", "India", "Delhi", 28.6139, 77.2090, 216, ["inland", "hot"]),
    ("Dhaka", "Bangladesh", "Dhaka", 23.8103, 90.4125, 4, ["inland", "hot"]),
    ("Bangkok", "Thailand", "Bangkok", 13.7563, 100.5018, 2, ["city", "hot"]),
    ("Singapore", "Singapore", "Central", 1.3521, 103.8198, 15, ["coastal", "hot"]),
    ("Tokyo", "Japan", "Kanto", 35.6762, 139.6503, 40, ["coastal", "city"]),
    ("Beijing", "China", "Beijing", 39.9042, 116.4074, 44, ["city", "inland"]),
    ("Sydney", "Australia", "New South Wales", -33.8688, 151.2093, 58, ["coastal"]),
    ("Auckland", "New Zealand", "Auckland", -36.8485, 174.7633, 20, ["coastal"]),
    ("New York", "USA", "New York", 40.7128, -74.0060, 10, ["coastal", "city"]),
    ("Denver", "USA", "Colorado", 39.7392, -104.9903, 1609, ["mountain", "inland"]),
    ("Los Angeles", "USA", "California", 34.0522, -118.2437, 93, ["coastal", "hot"]),
    ("Toronto", "Canada", "Ontario", 43.6532, -79.3832, 76, ["city", "cold"]),
    ("Mexico City", "Mexico", "CDMX", 19.4326, -99.1332, 2240, ["mountain", "city"]),
    ("Sao Paulo", "Brazil", "Sao Paulo", -23.5505, -46.6333, 760, ["city"]),
    ("Buenos Aires", "Argentina", "Buenos Aires", -34.6037, -58.3816, 25, ["coastal", "city"]),
]

DAILY = ("temperature_2m_max,temperature_2m_min,precipitation_sum,"
         "wind_speed_10m_max,relative_humidity_2m_mean,weather_code")


def condition(code):
    """Turn a weather code number into a simple word."""
    if code == 0: return "Clear"
    if code in (1, 2, 3): return "Cloudy"
    if code in (45, 48): return "Fog"
    if 51 <= code <= 67 or 80 <= code <= 82: return "Rain"
    if 71 <= code <= 77 or code in (85, 86): return "Snow"
    if code >= 95: return "Thunderstorm"
    return "Other"


def rows(daily):
    """Turn Open-Meteo's lists into a list of one dictionary per day."""
    n = len(daily["time"])
    get = lambda key: daily.get(key) or [None] * n
    tmax, tmin = get("temperature_2m_max"), get("temperature_2m_min")
    hum, wind = get("relative_humidity_2m_mean"), get("wind_speed_10m_max")
    rain, code = get("precipitation_sum"), get("weather_code")
    out = []
    for i, d in enumerate(daily["time"]):
        if tmax[i] is None or tmin[i] is None:
            continue                      # skip days with missing data
        out.append({
            "_id": ObjectId(),
            "date": d,
            "temp_max": tmax[i],
            "temp_min": tmin[i],
            "humidity": hum[i] if hum[i] is not None else 0,
            "wind_kph": wind[i] if wind[i] is not None else 0,
            "precip_mm": rain[i] if rain[i] is not None else 0,
            "condition": condition(code[i] or 0),
        })
    return out


def main():
    locations.delete_many({})             # start fresh each time
    end_obs = date.today() - timedelta(days=7)   # archive data lags a few days
    start_obs = end_obs - timedelta(days=60)

    for name, country, region, lat, lng, elev, tags in CITIES:
        try:
            f = requests.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lng, "daily": DAILY,
                "past_days": 60, "forecast_days": 14, "timezone": "auto"},
                timeout=30).json()
            a = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
                "latitude": lat, "longitude": lng, "daily": DAILY,
                "start_date": start_obs.isoformat(), "end_date": end_obs.isoformat(),
                "timezone": "auto"}, timeout=30).json()
            forecasts = rows(f["daily"])
            observations = rows(a["daily"])
        except Exception as e:            # one bad city shouldn't stop the rest
            print("FAILED", name, "-", e)
            continue

        for o in observations:
            o["user"] = "openmeteo-archive"
            o["comment"] = "Imported archive data"
            o["created"] = date.today().isoformat()

        locations.insert_one({
            "name": name, "country": country, "region": region,
            "geo": {"type": "Point", "coordinates": [lng, lat]},   # GeoJSON order is [lng, lat]
            "elevation_m": elev, "tags": tags, "timezone": f.get("timezone"),
            "forecasts": forecasts, "observations": observations,
        })
        print("imported", name, "-", len(forecasts), "forecasts,", len(observations), "observations")

    create_indexes()
    print("Done. Cities in database:", locations.count_documents({}))


if __name__ == "__main__":
    main()