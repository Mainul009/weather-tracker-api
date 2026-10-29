from flask import Blueprint, request, jsonify
from db import locations
from utils import to_oid, serialize, page_args
from validators import validate_location
from decorators import admin_required

locations_bp = Blueprint("locations", __name__)
LIST_PROJECTION = {"forecasts": 0, "observations": 0}   # keeps list responses small


@locations_bp.route("/locations", methods=["GET"])
def list_locations():
    pn, ps = page_args()
    if pn is None:
        return jsonify({"error": "pn and ps must be integers"}), 400

    a, q, elem = request.args, {}, {}
    if a.get("country"):
        q["country"] = a["country"]
    if a.get("region"):
        q["region"] = a["region"]
    if a.get("tag"):
        q["tags"] = {"$in": a.getlist("tag")}          # ?tag=coastal&tag=hot
    if a.get("q"):
        q["$text"] = {"$search": a["q"]}               # text search
    try:
        if a.get("min_temp"):
            elem["temp_max"] = {"$gte": float(a["min_temp"])}
        if a.get("max_temp"):
            elem.setdefault("temp_max", {})["$lte"] = float(a["max_temp"])
    except ValueError:
        return jsonify({"error": "min_temp and max_temp must be numbers"}), 400
    if a.get("condition"):
        elem["condition"] = a["condition"]
    if a.get("date"):
        elem["date"] = a["date"]
    if elem:
        q["forecasts"] = {"$elemMatch": elem}   # all conditions must match the SAME forecast

    sort_field = a.get("sort") if a.get("sort") in ("name", "country") else "name"
    direction = -1 if a.get("order") == "desc" else 1

    total = locations.count_documents(q)
    cur = (locations.find(q, LIST_PROJECTION).sort(sort_field, direction)
           .skip((pn - 1) * ps).limit(ps))
    return jsonify({"data": serialize(list(cur)), "page": pn, "page_size": ps,
                    "total": total, "total_pages": -(-total // ps)}), 200


@locations_bp.route("/locations/nearby", methods=["GET"])
def nearby():
    try:
        lat, lng = float(request.args["lat"]), float(request.args["lng"])
        km = float(request.args.get("radius_km", 100))
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lng are required numbers; radius_km must be a number"}), 400
    cur = locations.find({"geo": {"$near": {
        "$geometry": {"type": "Point", "coordinates": [lng, lat]},
        "$maxDistance": km * 1000}}}, LIST_PROJECTION).limit(20)
    return jsonify(serialize(list(cur))), 200


@locations_bp.route("/locations/<lid>", methods=["GET"])
def get_location(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    doc = locations.find_one({"_id": oid})
    if not doc:
        return jsonify({"error": "Location not found"}), 404
    return jsonify(serialize(doc)), 200


@locations_bp.route("/locations", methods=["POST"])
@admin_required
def add_location():
    d = request.get_json(silent=True)
    errors = validate_location(d)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400
    doc = {"name": d["name"].strip(), "country": d["country"], "region": d.get("region", ""),
           "geo": {"type": "Point", "coordinates": [d["lng"], d["lat"]]},
           "elevation_m": d.get("elevation_m", 0), "tags": d.get("tags", []),
           "forecasts": [], "observations": []}
    new_id = locations.insert_one(doc).inserted_id
    return jsonify({"id": str(new_id), "url": f"/api/v1/locations/{new_id}"}), 201


@locations_bp.route("/locations/<lid>", methods=["PUT"])
@admin_required
def edit_location(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    d = request.get_json(silent=True)
    errors = validate_location(d, partial=True)
    if errors or not d:
        return jsonify({"error": "Validation failed",
                        "details": errors or {"body": "cannot be empty"}}), 400
    upd = {k: d[k] for k in ("name", "country", "region", "elevation_m", "tags") if k in d}
    if "lat" in d or "lng" in d:
        cur = locations.find_one({"_id": oid}, {"geo": 1})
        if not cur:
            return jsonify({"error": "Location not found"}), 404
        lng0, lat0 = cur["geo"]["coordinates"]
        upd["geo"] = {"type": "Point", "coordinates": [d.get("lng", lng0), d.get("lat", lat0)]}
    if not upd:
        return jsonify({"error": "Validation failed",
                        "details": {"body": "no updatable fields"}}), 400
    r = locations.update_one({"_id": oid}, {"$set": upd})
    if r.matched_count == 0:
        return jsonify({"error": "Location not found"}), 404
    return jsonify({"message": "Location updated"}), 200


@locations_bp.route("/locations/<lid>", methods=["DELETE"])
@admin_required
def delete_location(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    if locations.delete_one({"_id": oid}).deleted_count == 0:
        return jsonify({"error": "Location not found"}), 404
    return "", 204