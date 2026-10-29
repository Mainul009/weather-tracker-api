from flask import Blueprint
auth_bp = Blueprint("auth", __name__)

import re
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, g
from pymongo.errors import DuplicateKeyError
from db import users, blacklist
from config import SECRET_KEY, TOKEN_HOURS
from decorators import jwt_required

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    u, e, p = data.get("username"), data.get("email"), data.get("password")

    errors = {}
    if not isinstance(u, str) or not 3 <= len(u) <= 30 or not u.replace("_", "").isalnum():
        errors["username"] = "3-30 characters: letters, digits, underscore"
    if not isinstance(e, str) or not EMAIL_RE.match(e):
        errors["email"] = "must be a valid email address"
    if not isinstance(p, str) or len(p) < 8:
        errors["password"] = "must be at least 8 characters"
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt())   # scrambles the password
    try:
        users.insert_one({"username": u, "email": e.lower(), "password": hashed,
                          "role": "user", "tracked_locations": [], "units": "metric"})
    except DuplicateKeyError:
        return jsonify({"error": "Username or email already exists"}), 409
    return jsonify({"message": "User registered"}), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    pw = data.get("password", "")
    user = users.find_one({"username": data.get("username", "")})
    if not user or not isinstance(pw, str) or not bcrypt.checkpw(pw.encode(), user["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    token = jwt.encode({"sub": user["username"], "role": user["role"], "exp": expires},
                       SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token}), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required
def logout():
    expires = datetime.fromtimestamp(g.user["exp"], tz=timezone.utc)
    blacklist.insert_one({"token": g.token, "expires": expires})
    return jsonify({"message": "Logged out"}), 200