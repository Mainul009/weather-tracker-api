from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from flask import request

def to_oid(value):
    """Turn a string into a MongoDB id, or return None if it's not a valid id."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None

def serialize(obj):
    """Convert MongoDB data into something that can be sent as JSON."""
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def page_args(default_size=10, max_size=100):
    """Read ?pn=2&ps=10 from the URL. Returns (None, None) if they aren't numbers."""
    try:
        pn = max(int(request.args.get("pn", 1)), 1)
        ps = min(max(int(request.args.get("ps", default_size)), 1), max_size)
    except ValueError:
        return None, None
    return pn, ps