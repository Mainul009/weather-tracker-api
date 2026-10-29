from datetime import date
from bson import ObjectId
from flask import Blueprint, request, jsonify, g
from db import locations
from utils import to_oid, serialize
from validators import validate_observation
from decorators import jwt_required

observations_bp = Blueprint("observations", __name__)


@observations_bp.route("/locations/<lid>/observations", methods=["GET"])
def list_observations(lid):
    oid = to_oid(lid)
    if not oid:
        return jsonify({"error": "Invalid location id"}), 400
    doc = locations.find_one({"_id": oid}, {"observations": 1})
    if not doc:
        return jsonify({"error": "Location not found"}), 404
    obs = sorted(doc["observations"], key=lambda o: o["date"], reverse=True)
    if request.args.get("user"):                      # ?user=alice
        obs = [o for o in obs if o.get("user") == request.args["user"]]
    return jsonify(serialize(obs)), 200


@observations_bp.route("/locations/<lid>/observations/<obs_id>", methods=["GET"])
def get_observation(lid, obs_id):
    l, o = to_oid(lid), to_oid(obs_id)
    if not l or not o:
        return jsonify({"error": "Invalid id"}), 400
    doc = locations.find_one({"_id": l, "observations._id": o}, {"observations.$": 1})
    if not doc:
        return jsonify({"error": "Observation not found"}), 404
    return jsonify(serialize(doc["observations"][0])), 200


@observations_bp.route("/locations/<lid>/observations", methods=["POST"])
@jwt_required
def add_observation(lid):
    l = to_oid(lid)
    if not l:
        return jsonify({"error": "Invalid location id"}), 400
    d = request.get_json(silent=True)
    errors = validate_observation(d)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    d["_id"] = ObjectId()
    d["user"] = g.user["sub"]                         # username comes from the token
    d["created"] = date.today().isoformat()

    # one observation per user per date
    r = locations.update_one(
        {"_id": l, "observations": {"$not": {"$elemMatch": {"date": d["date"], "user": d["user"]}}}},
        {"$push": {"observations": d}})
    if r.matched_count == 0:
        if locations.count_documents({"_id": l}) == 0:
            return jsonify({"error": "Location not found"}), 404
        return jsonify({"error": "You already logged an observation for that date"}), 409
    return jsonify({"id": str(d["_id"]),
                    "url": f"/api/v1/locations/{lid}/observations/{d['_id']}"}), 201


def owner_filter(l, o):
    """Matches the observation only if the caller owns it (admins can touch any)."""
    elem = {"_id": o}
    if g.user.get("role") != "admin":
        elem["user"] = g.user["sub"]
    return {"_id": l, "observations": {"$elemMatch": elem}}


def forbidden_or_missing(l, o):
    """Used when the owner check failed: was it someone else's, or does it not exist?"""
    if locations.count_documents({"_id": l, "observations._id": o}):
        return jsonify({"error": "You can only modify your own observations"}), 403
    return jsonify({"error": "Observation not found"}), 404


@observations_bp.route("/locations/<lid>/observations/<obs_id>", methods=["PUT"])
@jwt_required
def edit_observation(lid, obs_id):
    l, o = to_oid(lid), to_oid(obs_id)
    if not l or not o:
        return jsonify({"error": "Invalid id"}), 400
    d = request.get_json(silent=True)
    errors = validate_observation(d, partial=True)
    if errors or not d:
        return jsonify({"error": "Validation failed",
                        "details": errors or {"body": "cannot be empty"}}), 400
    upd = {f"observations.$.{k}": v for k, v in d.items()}
    if locations.update_one(owner_filter(l, o), {"$set": upd}).matched_count == 0:
        return forbidden_or_missing(l, o)
    return jsonify({"message": "Observation updated"}), 200


@observations_bp.route("/locations/<lid>/observations/<obs_id>", methods=["DELETE"])
@jwt_required
def delete_observation(lid, obs_id):
    l, o = to_oid(lid), to_oid(obs_id)
    if not l or not o:
        return jsonify({"error": "Invalid id"}), 400
    r = locations.update_one(owner_filter(l, o), {"$pull": {"observations": {"_id": o}}})
    if r.matched_count == 0:
        return forbidden_or_missing(l, o)
    return "", 204