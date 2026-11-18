import json
from typing import Any

from backend.database import execute, fetch_all, fetch_one, transaction


ITEM_SELECT = """
SELECT
    i.item_id,
    i.category_id,
    i.item_type,
    i.title,
    i.description,
    i.item_url,
    i.attributes,
    i.created_at,
    c.name AS category_name,
    c.parent_category_id,
    COALESCE(r.average_rating, 0) AS average_rating,
    COALESCE(r.rating_count, 0) AS rating_count,
    COALESCE(s.is_saved, 0) AS is_saved,
    mine.rating AS user_rating,
    COALESCE(pop.interaction_count, 0) AS interaction_count
FROM items AS i
JOIN categories AS c ON c.category_id = i.category_id
LEFT JOIN (
    SELECT item_id, AVG(rating) AS average_rating, COUNT(*) AS rating_count
    FROM ratings
    GROUP BY item_id
) AS r ON r.item_id = i.item_id
LEFT JOIN (
    SELECT item_id, COUNT(*) AS interaction_count
    FROM interactions
    GROUP BY item_id
) AS pop ON pop.item_id = i.item_id
LEFT JOIN (
    SELECT item_id, 1 AS is_saved
    FROM saved_items
    WHERE user_id = %s
) AS s ON s.item_id = i.item_id
LEFT JOIN ratings AS mine ON mine.item_id = i.item_id AND mine.user_id = %s
"""


def serialize_item(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    attributes = item.get("attributes")
    if isinstance(attributes, str):
        item["attributes"] = json.loads(attributes)
    item["average_rating"] = float(item.get("average_rating") or 0)
    item["rating_count"] = int(item.get("rating_count") or 0)
    item["interaction_count"] = int(item.get("interaction_count") or 0)
    item["is_saved"] = bool(item.get("is_saved"))
    if item.get("user_rating") is not None:
        item["user_rating"] = int(item["user_rating"])
    return item


def get_user(user_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT user_id, username, display_name, email
        FROM users
        WHERE user_id = %s AND is_active = TRUE
        """,
        (user_id,),
    )


def get_user_for_auth(identifier: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT user_id, username, email, display_name, password_hash
        FROM users
        WHERE (username = %s OR email = %s) AND is_active = TRUE
        LIMIT 1
        """,
        (identifier, identifier),
    )


def account_exists(username: str, email: str) -> bool:
    return fetch_one(
        "SELECT user_id FROM users WHERE username = %s OR email = %s LIMIT 1",
        (username, email),
    ) is not None


def create_user(
    username: str,
    email: str,
    display_name: str,
    password_hash: str,
) -> int:
    with transaction() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, email, display_name, password_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (username, email, display_name, password_hash),
            )
            return int(cursor.lastrowid)
        finally:
            cursor.close()


def list_users() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT user_id, username, display_name
        FROM users
        WHERE is_active = TRUE
        ORDER BY display_name
        """
    )


def list_categories() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT category_id, parent_category_id, name, slug, description
        FROM categories
        ORDER BY name
        """
    )


def list_catalog(
    user_id: int | None,
    search: str = "",
    category_id: int | None = None,
    item_type: str = "",
    sort: str = "recommended",
    limit: int = 48,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = ITEM_SELECT + " WHERE i.is_active = TRUE"
    params: list[Any] = [user_id or 0, user_id or 0]
    if search:
        query += " AND (i.title LIKE %s OR i.description LIKE %s OR c.name LIKE %s)"
        term = f"%{search}%"
        params.extend((term, term, term))
    if category_id is not None:
        query += " AND (i.category_id = %s OR c.parent_category_id = %s)"
        params.extend((category_id, category_id))
    if item_type:
        query += " AND i.item_type = %s"
        params.append(item_type)

    ordering = {
        "rating": "average_rating DESC, i.title",
        "newest": "i.created_at DESC, i.title",
        "popular": "interaction_count DESC, average_rating DESC, i.title",
        "recommended": "average_rating DESC, interaction_count DESC, i.title",
    }.get(sort, "average_rating DESC, interaction_count DESC, i.title")
    query += f" ORDER BY {ordering} LIMIT %s OFFSET %s"
    params.extend((limit, offset))
    return [serialize_item(row) for row in fetch_all(query, tuple(params))]


def get_catalog_item(item_id: int, user_id: int | None = None) -> dict[str, Any] | None:
    rows = fetch_all(
        ITEM_SELECT + " WHERE i.is_active = TRUE AND i.item_id = %s",
        (user_id or 0, user_id or 0, item_id),
    )
    return serialize_item(rows[0]) if rows else None


def list_saved_items(user_id: int) -> list[dict[str, Any]]:
    query = ITEM_SELECT + """
    JOIN saved_items AS saved ON saved.item_id = i.item_id AND saved.user_id = %s
    WHERE i.is_active = TRUE
    ORDER BY saved.saved_at DESC
    """
    rows = fetch_all(query, (user_id, user_id, user_id))
    return [serialize_item(row) for row in rows]


def list_user_interests(user_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT c.category_id, c.name, c.parent_category_id, ui.interest_weight
        FROM user_interests AS ui
        JOIN categories AS c ON c.category_id = ui.category_id
        WHERE ui.user_id = %s
        ORDER BY c.name
        """,
        (user_id,),
    )
    for row in rows:
        row["interest_weight"] = float(row["interest_weight"])
    return rows


def get_profile_stats(user_id: int) -> dict[str, int]:
    row = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM interactions WHERE user_id = %s) AS interaction_count,
            (SELECT COUNT(*) FROM ratings WHERE user_id = %s) AS rating_count,
            (SELECT COUNT(*) FROM saved_items WHERE user_id = %s) AS saved_count,
            (SELECT COUNT(*) FROM user_interests WHERE user_id = %s) AS interest_count
        """,
        (user_id, user_id, user_id, user_id),
    )
    return {key: int(value) for key, value in row.items()} if row else {}


def list_recommendation_history(user_id: int, limit: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            rh.run_id,
            rh.item_id,
            rh.score,
            rh.rank_position,
            rh.algorithm_name,
            rh.generated_at,
            i.title,
            i.item_type,
            i.description,
            i.attributes,
            c.name AS category_name
        FROM recommendation_history AS rh
        JOIN items AS i ON i.item_id = rh.item_id
        JOIN categories AS c ON c.category_id = i.category_id
        WHERE rh.user_id = %s
        ORDER BY rh.generated_at DESC, rh.rank_position ASC
        LIMIT %s
        """,
        (user_id, limit),
    )
    for row in rows:
        row["score"] = float(row["score"])
        if isinstance(row.get("attributes"), str):
            row["attributes"] = json.loads(row["attributes"])
    return rows


def load_graph_snapshot(user_id: int) -> dict[str, list[dict[str, Any]]]:
    return {
        "items": list_catalog(user_id, limit=10000),
        "interactions": fetch_all(
            "SELECT user_id, item_id, interaction_type, strength FROM interactions"
        ),
        "ratings": fetch_all("SELECT user_id, item_id, rating FROM ratings"),
        "saved_items": fetch_all("SELECT user_id, item_id FROM saved_items"),
        "interests": fetch_all(
            "SELECT user_id, category_id, interest_weight FROM user_interests"
        ),
        "categories": list_categories(),
    }


def save_recommendation_run(rows: list[tuple]) -> None:
    if not rows:
        return
    with transaction() as connection:
        cursor = connection.cursor()
        try:
            cursor.executemany(
                """
                INSERT INTO recommendation_history
                    (run_id, user_id, item_id, score, rank_position, algorithm_name)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
        finally:
            cursor.close()


def save_user_interests(user_id: int, interests: list[tuple[int, float]]) -> None:
    with transaction() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM user_interests WHERE user_id = %s", (user_id,))
            if interests:
                cursor.executemany(
                    """
                    INSERT INTO user_interests (user_id, category_id, interest_weight)
                    VALUES (%s, %s, %s)
                    """,
                    [(user_id, category_id, weight) for category_id, weight in interests],
                )
        finally:
            cursor.close()


def category_ids_exist(category_ids: list[int]) -> set[int]:
    if not category_ids:
        return set()
    placeholders = ", ".join(["%s"] * len(category_ids))
    rows = fetch_all(
        f"SELECT category_id FROM categories WHERE category_id IN ({placeholders})",
        tuple(category_ids),
    )
    return {int(row["category_id"]) for row in rows}


def user_exists(user_id: int) -> bool:
    return get_user(user_id) is not None
