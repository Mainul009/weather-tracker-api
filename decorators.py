from functools import wraps
import jwt
from flask import request, jsonify, g
from config import SECRET_KEY
from db import blacklist

def jwt_required(f):
    """Put @jwt_required above a route to make it need a valid login token."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        if blacklist.find_one({"token": token}):
            return jsonify({"error": "Token has been revoked"}), 401
        try:
            g.user = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.token = token
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """Like jwt_required, but the user must also be an admin."""
    @wraps(f)
    @jwt_required
    def wrapper(*args, **kwargs):
        if g.user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper