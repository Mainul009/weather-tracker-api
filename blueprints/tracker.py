from datetime import date
from flask import Blueprint, jsonify, g
from db import users, locations
from utils import to_oid, serialize
from decorators import jwt_required

tracker_bp = Blueprint("tracker", __name__)


@tracker_bp.route("/users/me/tracked/<lid>", methods=["POST"])
@jwt_required
def track(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    if locations.count_documents({"_id": oid}) == 0:
        return jsonify({"error": "Location not found"}), 404
    # $addToSet adds the id only if it isn't already in the list
    users.update_one({"username": g.user["sub"]}, {"$addToSet": {"tracked_locations": oid}})
    return jsonify({"message": "Location tracked"}), 201


@tracker_bp.route("/users/me/tracked/<lid>", methods=["DELETE"])
@jwt_required
def untrack(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    r = users.update_one({"username": g.user["sub"], "tracked_locations": oid},
                         {"$pull": {"tracked_locations": oid}})
    if r.modified_count == 0:
        return jsonify({"error": "Location is not tracked"}), 404
    return "", 204


@tracker_bp.route("/users/me/tracker", methods=["GET"])
@jwt_required
def dashboard():
    """Each tracked city, its next forecast, and this user's alerts for it."""
    me = users.find_one({"username": g.user["sub"]}, {"tracked_locations": 1})
    if not me:
        return jsonify({"error": "User not found"}), 404
    today = date.today().isoformat()
    res = locations.aggregate([
        {"$match": {"_id": {"$in": me.get("tracked_locations", [])}}},
        # $lookup joins this city with the alerts collection
        {"$lookup": {"from": "alerts",
                     "let": {"lid": "$_id", "u": g.user["sub"]},
                     "pipeline": [{"$match": {"$expr": {"$and": [
                         {"$eq": ["$location_id", "$$lid"]},
                         {"$eq": ["$user", "$$u"]}]}}}],
                     "as": "my_alerts"}},
        {"$project": {"name": 1, "country": 1, "my_alerts": 1,
                      "next_forecast": {"$first": {"$filter": {
                          "input": "$forecasts", "as": "f",
                          "cond": {"$gte": ["$$f.date", today]}}}}}}])
    return jsonify(serialize(list(res))), 200