import math
import re
import secrets
import sqlite3
from hmac import compare_digest
from typing import Any

from flask import Blueprint, g, jsonify, request, session
from werkzeug.exceptions import BadRequest
from werkzeug.security import check_password_hash, generate_password_hash
from mysql.connector.errors import IntegrityError

from backend.database import execute, fetch_all, fetch_one, is_sqlite
from backend.engine.graph_recommender import recommend_for_user
from backend.models.repository import (
    account_exists,
    category_ids_exist,
    create_user,
    get_catalog_item,
    get_profile_stats,
    get_user,
    get_user_for_auth,
    list_categories,
    list_catalog,
    list_recommendation_history,
    list_saved_items,
    list_user_interests,
    save_user_interests,
)


api = Blueprint("api", __name__, url_prefix="/api")
INTERACTION_TYPES = {"view", "click", "like", "share", "purchase", "dismiss"}
PUBLIC_ENDPOINTS = {
    "api.health",
    "api.categories",
    "api.csrf_token",
    "api.auth_me",
    "api.register",
    "api.login",
    "api.logout",
}


def _error(message: str, status: int):
    return jsonify({"error": message}), status


def _body() -> dict[str, Any] | None:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _valid_positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        converted = value
    elif isinstance(value, str) and value.isdecimal():
        converted = int(value)
    else:
        return None
    return converted if converted > 0 else None


def _limit(default: int, maximum: int) -> int:
    raw = request.args.get("limit")
    if raw is None:
        return default
    parsed = _valid_positive_int(raw)
    if parsed is None:
        raise BadRequest("limit must be a positive integer.")
    return min(parsed, maximum)


def _session_response(user: dict[str, Any], status: int = 200):
    session.clear()
    session.permanent = True
    session["user_id"] = int(user["user_id"])
    session["csrf_token"] = secrets.token_urlsafe(32)
    return jsonify(
        {
            "authenticated": True,
            "user": user,
            "csrf_token": session["csrf_token"],
        }
    ), status


@api.before_request
def enforce_session_and_csrf():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected = session.get("csrf_token", "")
        supplied = request.headers.get("X-CSRF-Token", "")
        if not expected or not supplied or not compare_digest(expected, supplied):
            return _error("A valid CSRF token is required.", 400)

    if request.endpoint in PUBLIC_ENDPOINTS:
        return None
    user_id = session.get("user_id")
    if not isinstance(user_id, int):
        return _error("Please sign in to continue.", 401)
    user = get_user(user_id)
    if user is None:
        session.clear()
        return _error("Your account is unavailable. Please sign in again.", 401)
    g.current_user = user
    return None


@api.after_request
def prevent_api_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@api.get("/health")
def health():
    if is_sqlite():
        row = fetch_one("SELECT sqlite_version() AS database_version")
        return jsonify(
            {
                "status": "ok",
                "database": "sqlite demo",
                "database_version": row["database_version"],
            }
        )
    row = fetch_one("SELECT VERSION() AS mysql_version")
    return jsonify({"status": "ok", "database": "connected", "mysql_version": row["mysql_version"]})


@api.get("/auth/csrf")
def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return jsonify({"csrf_token": token})


@api.get("/auth/me")
def auth_me():
    user_id = session.get("user_id")
    user = get_user(user_id) if isinstance(user_id, int) else None
    if user_id is not None and user is None:
        session.clear()
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return jsonify({"authenticated": user is not None, "user": user, "csrf_token": token})


@api.post("/auth/register")
def register():
    data = _body()
    if data is None:
        return _error("A JSON object is required.", 400)
    username = data.get("username")
    email = data.get("email")
    display_name = data.get("display_name")
    password = data.get("password")
    if not all(isinstance(value, str) for value in (username, email, display_name, password)):
        return _error("Username, email, display_name, and password are required.", 400)

    username = username.strip()
    email = email.strip().lower()
    display_name = display_name.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,50}", username):
        return _error("Username must be 3–50 characters using letters, numbers, '.', '_' or '-'.", 400)
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return _error("Enter a valid email address.", 400)
    if not display_name or len(display_name) > 120:
        return _error("Display name must be between 1 and 120 characters.", 400)
    if len(password) < 12 or len(password) > 128:
        return _error("Password must be between 12 and 128 characters.", 400)
    if account_exists(username, email):
        return _error("That username or email is already registered.", 409)

    try:
        user_id = create_user(
            username,
            email,
            display_name,
            generate_password_hash(password),
        )
    except (IntegrityError, sqlite3.IntegrityError):
        return _error("That username or email is already registered.", 409)
    user = get_user(user_id)
    return _session_response(user, 201)


@api.post("/auth/login")
def login():
    data = _body()
    if data is None:
        return _error("A JSON object is required.", 400)
    identifier = data.get("identifier")
    password = data.get("password")
    if not isinstance(identifier, str) or not isinstance(password, str):
        return _error("Username or email and password are required.", 400)
    identifier = identifier.strip()
    if not identifier or len(identifier) > 254 or len(password) > 256:
        return _error("Invalid username/email or password.", 401)

    account = get_user_for_auth(identifier)
    password_hash = account.get("password_hash") if account else None
    if not password_hash or not check_password_hash(password_hash, password):
        return _error("Invalid username/email or password.", 401)
    user = get_user(int(account["user_id"]))
    return _session_response(user)


@api.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"authenticated": False})


@api.get("/users")
def users():
    return jsonify({"users": [g.current_user]})


@api.get("/categories")
def categories():
    return jsonify({"categories": list_categories()})


@api.get("/catalog")
def catalog():
    requested_user_id = request.args.get("user_id")
    parsed_user_id = int(g.current_user["user_id"])
    if requested_user_id and _valid_positive_int(requested_user_id) is None:
        return _error("user_id must be a positive integer.", 400)
    if requested_user_id and int(requested_user_id) != parsed_user_id:
        return _error("You cannot access another account's catalog.", 403)

    raw_category = request.args.get("category_id")
    category_id = _valid_positive_int(raw_category) if raw_category else None
    if raw_category and category_id is None:
        return _error("category_id must be a positive integer.", 400)

    search = request.args.get("search", "").strip()[:120]
    item_type = request.args.get("type", "").strip()[:40]
    sort = request.args.get("sort", "recommended")
    try:
        raw_offset = request.args.get("offset", "0")
        if not raw_offset.isdecimal():
            raise ValueError
        offset = int(raw_offset)
    except ValueError:
        return _error("offset must be a non-negative integer.", 400)

    items = list_catalog(
        parsed_user_id,
        search=search,
        category_id=category_id,
        item_type=item_type,
        sort=sort,
        limit=_limit(48, 100),
        offset=offset,
    )
    return jsonify({"items": items, "count": len(items)})


@api.get("/dashboard")
def dashboard():
    requested_user_id = request.args.get("user_id")
    user_id = _valid_positive_int(requested_user_id) if requested_user_id else int(g.current_user["user_id"])
    if user_id is None:
        return _error("A positive user_id is required.", 400)
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot access another account's recommendations.", 403)
    user = g.current_user

    result = recommend_for_user(user_id, limit=_limit(8, 24))
    return jsonify(
        {
            "user": user,
            "stats": get_profile_stats(user_id),
            "run_id": result["run_id"],
            "algorithm": result["algorithm"],
            "recommendations": result["recommendations"],
        }
    )


@api.get("/history")
def recommendation_history():
    requested_user_id = request.args.get("user_id")
    user_id = _valid_positive_int(requested_user_id) if requested_user_id else int(g.current_user["user_id"])
    if user_id is None:
        return _error("A positive user_id is required.", 400)
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot access another account's history.", 403)
    history = list_recommendation_history(user_id, _limit(50, 200))
    return jsonify({"history": history, "count": len(history)})


@api.get("/users/<int:user_id>/saved-items")
def saved_items(user_id: int):
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot access another account's saved items.", 403)
    items = list_saved_items(user_id)
    return jsonify({"items": items, "count": len(items)})


@api.route("/users/<int:user_id>/saved-items/<int:item_id>", methods=["POST", "DELETE"])
def update_saved_item(user_id: int, item_id: int):
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot change another account's saved items.", 403)
    if request.method == "DELETE":
        execute(
            "DELETE FROM saved_items WHERE user_id = %s AND item_id = %s",
            (user_id, item_id),
        )
        return jsonify({"saved": False, "item_id": item_id})

    if get_catalog_item(item_id) is None:
        return _error("That item does not exist or is inactive.", 404)
    if is_sqlite():
        query = """
            INSERT INTO saved_items (user_id, item_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, item_id)
            DO UPDATE SET saved_at = CURRENT_TIMESTAMP
        """
    else:
        query = """
            INSERT INTO saved_items (user_id, item_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE saved_at = CURRENT_TIMESTAMP
        """
    execute(query, (user_id, item_id))
    return jsonify({"saved": True, "item_id": item_id})


@api.post("/users/<int:user_id>/ratings")
def rate_item(user_id: int):
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot rate items for another account.", 403)
    data = _body()
    if data is None:
        return _error("A JSON object is required.", 400)
    item_id = _valid_positive_int(data.get("item_id"))
    rating = data.get("rating")
    if item_id is None or isinstance(rating, bool) or not isinstance(rating, int):
        return _error("item_id and an integer rating from 1 to 5 are required.", 400)
    if rating < 1 or rating > 5:
        return _error("rating must be between 1 and 5.", 400)
    review_text = data.get("review_text", "")
    if not isinstance(review_text, str) or len(review_text) > 1000:
        return _error("review_text must be a string of at most 1000 characters.", 400)
    if get_catalog_item(item_id) is None:
        return _error("That item does not exist or is inactive.", 404)

    if is_sqlite():
        query = """
            INSERT INTO ratings (user_id, item_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, item_id)
            DO UPDATE SET
                rating = excluded.rating,
                review_text = excluded.review_text,
                updated_at = CURRENT_TIMESTAMP
        """
    else:
        query = """
            INSERT INTO ratings (user_id, item_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                rating = VALUES(rating),
                review_text = VALUES(review_text),
                updated_at = CURRENT_TIMESTAMP
        """
    execute(query, (user_id, item_id, rating, review_text.strip() or None))
    return jsonify({"item_id": item_id, "rating": rating})


@api.post("/users/<int:user_id>/interactions")
def record_interaction(user_id: int):
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot record activity for another account.", 403)
    data = _body()
    if data is None:
        return _error("A JSON object is required.", 400)
    item_id = _valid_positive_int(data.get("item_id"))
    interaction_type = data.get("interaction_type")
    if (
        item_id is None
        or not isinstance(interaction_type, str)
        or interaction_type not in INTERACTION_TYPES
    ):
        return _error("item_id and a supported interaction_type are required.", 400)
    raw_strength = data.get("strength", 1)
    if isinstance(raw_strength, bool):
        return _error("strength must be a number greater than 0.", 400)
    try:
        strength = float(raw_strength)
    except (TypeError, ValueError):
        return _error("strength must be a number greater than 0.", 400)
    if not math.isfinite(strength) or strength <= 0 or strength > 9999.999:
        return _error("strength must be greater than 0 and no greater than 9999.999.", 400)
    if get_catalog_item(item_id) is None:
        return _error("That item does not exist or is inactive.", 404)

    execute(
        """
        INSERT INTO interactions (user_id, item_id, interaction_type, strength)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, item_id, interaction_type, strength),
    )
    return jsonify({"recorded": True, "item_id": item_id})


@api.get("/users/<int:user_id>/interests")
def interests(user_id: int):
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot access another account's interests.", 403)
    return jsonify({"interests": list_user_interests(user_id)})


@api.put("/users/<int:user_id>/interests")
def replace_interests(user_id: int):
    if user_id != int(g.current_user["user_id"]):
        return _error("You cannot change another account's interests.", 403)
    data = _body()
    if data is None or not isinstance(data.get("interests"), list):
        return _error("A JSON object with an interests array is required.", 400)

    normalized: list[tuple[int, float]] = []
    seen_category_ids: set[int] = set()
    for interest in data["interests"]:
        if not isinstance(interest, dict):
            return _error("Each interest must include category_id and weight.", 400)
        category_id = _valid_positive_int(interest.get("category_id"))
        raw_weight = interest.get("weight")
        if category_id is None or isinstance(raw_weight, bool):
            return _error("Each interest must include a valid category_id and weight.", 400)
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            return _error("Interest weight must be a number greater than 0 and at most 1.", 400)
        if not math.isfinite(weight) or not 0 < weight <= 1:
            return _error("Interest weight must be greater than 0 and at most 1.", 400)
        if category_id in seen_category_ids:
            return _error("A category can only appear once in the interests array.", 400)
        seen_category_ids.add(category_id)
        normalized.append((category_id, weight))

    existing_ids = category_ids_exist([category_id for category_id, _ in normalized])
    if existing_ids != seen_category_ids:
        return _error("One or more selected categories do not exist.", 400)
    save_user_interests(user_id, normalized)
    return jsonify({"interests": list_user_interests(user_id)})
