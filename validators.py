from datetime import datetime

CONDITIONS = {"Clear", "Cloudy", "Fog", "Rain", "Snow", "Thunderstorm", "Other"}
RANGES = {"temp_max": (-90, 60), "temp_min": (-90, 60), "humidity": (0, 100),
          "wind_kph": (0, 500), "precip_mm": (0, 2000)}
REQUIRED = ["date", "temp_max", "temp_min", "condition"]

def valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def validate_forecast(data, partial=False):
    """Returns {field: message}. An empty dict means the data is valid."""
    if not isinstance(data, dict):
        return {"body": "must be a JSON object"}
    errors = {}
    allowed = set(REQUIRED) | set(RANGES)
    for k in data:
        if k not in allowed:
            errors[k] = "unknown field"
    if not partial:
        for k in REQUIRED:
            if k not in data:
                errors[k] = "is required"
    if "date" in data and not valid_date(data["date"]):
        errors["date"] = "must be a valid date in YYYY-MM-DD format"
    for field, (lo, hi) in RANGES.items():
        if field in data:
            v = data[field]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errors[field] = "must be a number"
            elif not lo <= v <= hi:
                errors[field] = f"must be between {lo} and {hi}"
    if "condition" in data and data["condition"] not in CONDITIONS:
        errors["condition"] = f"must be one of {sorted(CONDITIONS)}"
    if (not errors and "temp_max" in data and "temp_min" in data
            and data["temp_min"] > data["temp_max"]):
        errors["temp_min"] = "cannot be greater than temp_max"
    return errors

def validate_observation(data, partial=False):
    """Same rules as a forecast, plus an optional comment."""
    if not isinstance(data, dict):
        return {"body": "must be a JSON object"}
    rest = {k: v for k, v in data.items() if k != "comment"}
    errors = validate_forecast(rest, partial)
    if "comment" in data and (not isinstance(data["comment"], str) or len(data["comment"]) > 500):
        errors["comment"] = "must be a string of at most 500 characters"
    return errors

def validate_location(data, partial=False):
    if not isinstance(data, dict):
        return {"body": "must be a JSON object"}
    errors = {}
    if not partial:
        for k in ("name", "country", "lat", "lng"):
            if k not in data:
                errors[k] = "is required"
    if "name" in data and (not isinstance(data["name"], str) or not data["name"].strip()):
        errors["name"] = "must be a non-empty string"
    if "lat" in data and not (isinstance(data["lat"], (int, float)) and -90 <= data["lat"] <= 90):
        errors["lat"] = "must be a number between -90 and 90"
    if "lng" in data and not (isinstance(data["lng"], (int, float)) and -180 <= data["lng"] <= 180):
        errors["lng"] = "must be a number between -180 and 180"
    return errors