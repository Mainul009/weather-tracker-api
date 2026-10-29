from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import locations
from utils import to_oid, serialize
from validators import validate_forecast
from decorators import admin_required

forecasts_bp = Blueprint("forecasts", __name__)


@forecasts_bp.route("/locations/<lid>/forecasts", methods=["GET"])
def list_forecasts(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    start = request.args.get("from", "0000-01-01")
    end = request.args.get("to", "9999-12-31")

    # $filter keeps only the forecasts whose date is between "from" and "to"
    res = list(locations.aggregate([
        {"$match": {"_id": oid}},
        {"$project": {"_id": 0, "forecasts": {"$filter": {
            "input": "$forecasts", "as": "f",
            "cond": {"$and": [{"$gte": ["$$f.date", start]},
                              {"$lte": ["$$f.date", end]}]}}}}}]))
    if not res:
        return jsonify({"error": "Location not found"}), 404
    ordered = sorted(res[0]["forecasts"], key=lambda f: f["date"])
    return jsonify(serialize(ordered)), 200


@forecasts_bp.route("/locations/<lid>/forecasts/<fid>", methods=["GET"])
def get_forecast(lid, fid):
    l, f = to_oid(lid), to_oid(fid)
    if not l or not f:
        return jsonify({"error": "Invalid id"}), 400
    # "forecasts.$" returns only the one matching item from the list
    doc = locations.find_one({"_id": l, "forecasts._id": f}, {"forecasts.$": 1})
    if not doc:
        return jsonify({"error": "Forecast not found"}), 404
    return jsonify(serialize(doc["forecasts"][0])), 200


@forecasts_bp.route("/locations/<lid>/forecasts", methods=["POST"])
@admin_required
def add_forecast(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    d = request.get_json(silent=True)
    errors = validate_forecast(d)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    d["_id"] = ObjectId()
    # only adds the forecast if that date isn't already in the list
    r = locations.update_one({"_id": oid, "forecasts.date": {"$ne": d["date"]}},
                             {"$push": {"forecasts": d}})
    if r.matched_count == 0:
        if locations.count_documents({"_id": oid}) == 0:
            return jsonify({"error": "Location not found"}), 404
        return jsonify({"error": "A forecast for that date already exists"}), 409
    return jsonify({"id": str(d["_id"]),
                    "url": f"/api/v1/locations/{lid}/forecasts/{d['_id']}"}), 201


@forecasts_bp.route("/locations/<lid>/forecasts/<fid>", methods=["PUT"])
@admin_required
def edit_forecast(lid, fid):
    l, f = to_oid(lid), to_oid(fid)
    if not l or not f:
        return jsonify({"error": "Invalid id"}), 400
    d = request.get_json(silent=True)
    errors = validate_forecast(d, partial=True)
    if errors or not d:
        return jsonify({"error": "Validation failed",
                        "details": errors or {"body": "cannot be empty"}}), 400

    # "forecasts.$.field" updates only the matching item in the list
    upd = {f"forecasts.$.{k}": v for k, v in d.items()}
    r = locations.update_one({"_id": l, "forecasts._id": f}, {"$set": upd})
    if r.matched_count == 0:
        return jsonify({"error": "Forecast not found"}), 404
    return jsonify({"message": "Forecast updated"}), 200


@forecasts_bp.route("/locations/<lid>/forecasts/<fid>", methods=["DELETE"])
@admin_required
def delete_forecast(lid, fid):
    l, f = to_oid(lid), to_oid(fid)
    if not l or not f:
        return jsonify({"error": "Invalid id"}), 400
    r = locations.update_one({"_id": l}, {"$pull": {"forecasts": {"_id": f}}})
    if r.modified_count == 0:
        return jsonify({"error": "Forecast not found"}), 404
    return "", 204