from flask import Blueprint, request, jsonify
from db import locations
from utils import to_oid, serialize

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/locations/<lid>/stats", methods=["GET"])
def stats(lid):
    """Average, highest, lowest temperature and total rain for a date range."""
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    start = request.args.get("from", "0000-01-01")
    end = request.args.get("to", "9999-12-31")

    res = list(locations.aggregate([
        {"$match": {"_id": oid}},                                  # pick the city
        {"$unwind": "$forecasts"},                                 # one row per forecast day
        {"$match": {"forecasts.date": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": "$_id", "name": {"$first": "$name"},    # combine the rows
                    "avg_max_c": {"$avg": "$forecasts.temp_max"},
                    "highest_c": {"$max": "$forecasts.temp_max"},
                    "lowest_c": {"$min": "$forecasts.temp_min"},
                    "total_rain_mm": {"$sum": "$forecasts.precip_mm"},
                    "max_wind_kph": {"$max": "$forecasts.wind_kph"},
                    "days": {"$sum": 1}}}]))
    if not res:
        return jsonify({"error": "No data for that location/range"}), 404
    return jsonify(serialize(res[0])), 200


@analytics_bp.route("/locations/<lid>/accuracy", methods=["GET"])
def accuracy(lid):
    """Compares each forecast with the observation for the same date."""
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400

    res = list(locations.aggregate([
        {"$match": {"_id": oid}},
        {"$unwind": "$forecasts"},                                 # one row per forecast
        # find the observation with the same date, inside the same city
        {"$set": {"obs": {"$first": {"$filter": {
            "input": "$observations", "as": "o",
            "cond": {"$eq": ["$$o.date", "$forecasts.date"]}}}}}},
        {"$match": {"obs": {"$exists": True}}},                    # keep days that have both
        {"$set": {"err": {"$abs": {"$subtract": ["$forecasts.temp_max", "$obs.temp_max"]}}}},
        {"$group": {"_id": "$_id", "name": {"$first": "$name"},
                    "days_compared": {"$sum": 1},
                    "mean_abs_error_c": {"$avg": "$err"},
                    "worst_error_c": {"$max": "$err"},
                    "within_2c": {"$sum": {"$cond": [{"$lte": ["$err", 2]}, 1, 0]}}}},
        {"$set": {"mean_abs_error_c": {"$round": ["$mean_abs_error_c", 2]},
                  "pct_within_2c": {"$round": [
                      {"$multiply": [{"$divide": ["$within_2c", "$days_compared"]}, 100]}, 1]}}}]))
    if not res:
        return jsonify({"error": "No overlapping forecast/observation dates"}), 404
    return jsonify(serialize(res[0])), 200


def ranking(field):
    """Shared by hottest, rainiest and windiest."""
    try:
        limit = min(max(int(request.args.get("limit", 10)), 1), 50)
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    match = {"country": request.args["country"]} if request.args.get("country") else {}
    op = "$sum" if field == "precip_mm" else "$avg"
    res = locations.aggregate([
        {"$match": match},
        {"$unwind": "$forecasts"},
        {"$group": {"_id": "$_id", "name": {"$first": "$name"},
                    "country": {"$first": "$country"},
                    "value": {op: f"$forecasts.{field}"}}},
        {"$sort": {"value": -1}},
        {"$limit": limit}])
    return jsonify(serialize(list(res))), 200


@analytics_bp.route("/analytics/hottest", methods=["GET"])
def hottest():
    return ranking("temp_max")


@analytics_bp.route("/analytics/rainiest", methods=["GET"])
def rainiest():
    return ranking("precip_mm")


@analytics_bp.route("/analytics/windiest", methods=["GET"])
def windiest():
    return ranking("wind_kph")


@analytics_bp.route("/analytics/condition-breakdown", methods=["GET"])
def condition_breakdown():
    """What percentage of all forecast days are Rain, Clear, and so on."""
    res = list(locations.aggregate([
        {"$unwind": "$forecasts"},
        {"$group": {"_id": "$forecasts.condition", "days": {"$sum": 1}}},
        {"$group": {"_id": None, "total": {"$sum": "$days"},
                    "items": {"$push": {"condition": "$_id", "days": "$days"}}}},
        {"$unwind": "$items"},
        {"$project": {"_id": 0, "condition": "$items.condition", "days": "$items.days",
                      "percent": {"$round": [
                          {"$multiply": [{"$divide": ["$items.days", "$total"]}, 100]}, 1]}}},
        {"$sort": {"days": -1}}]))
    return jsonify(res), 200