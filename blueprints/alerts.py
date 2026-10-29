from datetime import date, datetime, timezone
from flask import Blueprint, request, jsonify, g
from db import alerts, locations
from utils import to_oid, serialize
from decorators import jwt_required

alerts_bp = Blueprint("alerts", __name__)
METRICS = {"temp_max", "temp_min", "precip_mm", "wind_kph", "humidity"}
OPERATORS = {"gt", "lt"}          # gt = greater than, lt = less than


def validate_alert(d, partial=False):
    if not isinstance(d, dict):
        return {"body": "must be a JSON object"}
    errors = {}
    if not partial:
        for k in ("location_id", "metric", "operator", "threshold"):
            if k not in d:
                errors[k] = "is required"
    if "metric" in d and d["metric"] not in METRICS:
        errors["metric"] = f"must be one of {sorted(METRICS)}"
    if "operator" in d and d["operator"] not in OPERATORS:
        errors["operator"] = "must be 'gt' or 'lt'"
    if "threshold" in d and (isinstance(d["threshold"], bool)
                             or not isinstance(d["threshold"], (int, float))):
        errors["threshold"] = "must be a number"
    if "active" in d and not isinstance(d["active"], bool):
        errors["active"] = "must be true or false"
    return errors


@alerts_bp.route("/alerts", methods=["POST"])
@jwt_required
def create_alert():
    d = request.get_json(silent=True)
    errors = validate_alert(d)
    lid = to_oid(d.get("location_id")) if isinstance(d, dict) else None
    if isinstance(d, dict) and "location_id" in d and not lid:
        errors["location_id"] = "is not a valid id"
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400
    if locations.count_documents({"_id": lid}) == 0:
        return jsonify({"error": "Location not found"}), 404

    doc = {"user": g.user["sub"], "location_id": lid, "metric": d["metric"],
           "operator": d["operator"], "threshold": d["threshold"], "active": True,
           "created": datetime.now(timezone.utc)}
    new_id = alerts.insert_one(doc).inserted_id
    return jsonify({"id": str(new_id), "url": f"/api/v1/alerts/{new_id}"}), 201


@alerts_bp.route("/alerts", methods=["GET"])
@jwt_required
def list_alerts():
    return jsonify(serialize(list(alerts.find({"user": g.user["sub"]})))), 200


@alerts_bp.route("/alerts/<aid>", methods=["PUT"])
@jwt_required
def edit_alert(aid):
    a = to_oid(aid)
    if not a:
        return jsonify({"error": "Invalid alert id"}), 400
    d = request.get_json(silent=True)
    errors = validate_alert(d, partial=True)
    upd = {k: v for k, v in (d or {}).items()
           if k in ("metric", "operator", "threshold", "active")}
    if errors or not upd:
        return jsonify({"error": "Validation failed",
                        "details": errors or {"body": "no updatable fields"}}), 400
    # filtering by user means you can only change your own alerts
    r = alerts.update_one({"_id": a, "user": g.user["sub"]}, {"$set": upd})
    if r.matched_count == 0:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"message": "Alert updated"}), 200


@alerts_bp.route("/alerts/<aid>", methods=["DELETE"])
@jwt_required
def delete_alert(aid):
    a = to_oid(aid)
    if not a:
        return jsonify({"error": "Invalid alert id"}), 400
    if alerts.delete_one({"_id": a, "user": g.user["sub"]}).deleted_count == 0:
        return jsonify({"error": "Alert not found"}), 404
    return "", 204


@alerts_bp.route("/alerts/triggered", methods=["GET"])
@jwt_required
def triggered():
    """Active alerts whose condition is met by an upcoming forecast."""
    today, out = date.today().isoformat(), []
    for a in alerts.find({"user": g.user["sub"], "active": True}):
        loc = locations.find_one({"_id": a["location_id"]}, {"name": 1, "forecasts": 1})
        if not loc:
            continue
        for f in loc["forecasts"]:
            v = f.get(a["metric"])
            if v is None or f["date"] < today:
                continue
            hit = v > a["threshold"] if a["operator"] == "gt" else v < a["threshold"]
            if hit:
                out.append({"alert_id": a["_id"], "location": loc["name"], "date": f["date"],
                            "metric": a["metric"], "value": v,
                            "operator": a["operator"], "threshold": a["threshold"]})
    return jsonify(serialize(sorted(out, key=lambda x: x["date"]))), 200