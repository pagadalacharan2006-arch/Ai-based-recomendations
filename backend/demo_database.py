import json
import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    parent_category_id INTEGER,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    item_type TEXT NOT NULL DEFAULT 'product',
    title TEXT NOT NULL,
    description TEXT,
    item_url TEXT,
    attributes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS user_interests (
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    interest_weight REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, category_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL,
    strength REAL NOT NULL DEFAULT 1.0,
    occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    review_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_items (
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendation_history (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    score REAL NOT NULL,
    rank_position INTEGER NOT NULL,
    algorithm_name TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (run_id, user_id, item_id),
    UNIQUE (run_id, user_id, rank_position),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);
"""

CATEGORIES = (
    (1, None, "Books", "books", "Printed and digital books"),
    (2, None, "Technology", "technology", "Computers and consumer electronics"),
    (3, None, "Home and Garden", "home-garden", "Home improvement and gardening"),
    (4, None, "Outdoor", "outdoor", "Outdoor recreation and travel"),
    (5, 1, "Data Science", "data-science", "Data science and machine learning books"),
    (6, 2, "Photography", "photography", "Photography equipment and accessories"),
)

ITEMS = (
    (1, 5, "book", "Graph Machine Learning", "An introduction to learning with graph-structured data.", "https://example.test/items/1", {"format": "paperback", "language": "English"}),
    (2, 5, "book", "Practical Recommender Systems", "Methods for building and evaluating recommendation engines.", "https://example.test/items/2", {"format": "ebook", "language": "English"}),
    (3, 5, "course", "Introduction to Python for Data Analysis", "A hands-on course covering Python data analysis workflows.", "https://example.test/items/3", {"level": "beginner", "duration_hours": 8}),
    (4, 2, "product", "Developer Laptop 14", "A lightweight laptop suitable for programming and study.", "https://example.test/items/4", {"memory_gb": 16, "screen_inches": 14}),
    (5, 6, "product", "Mirrorless Camera X100", "A compact mirrorless camera for everyday photography.", "https://example.test/items/5", {"sensor": "APS-C", "color": "black"}),
    (6, 6, "product", "Portrait Lens 50mm", "A fast prime lens for portraits and low-light photography.", "https://example.test/items/6", {"focal_length_mm": 50, "mount": "X"}),
    (7, 3, "product", "Indoor Herb Garden Kit", "A starter kit for growing herbs in a sunny kitchen.", "https://example.test/items/7", {"plant_count": 6, "indoor": True}),
    (8, 4, "product", "Trail Daypack 20L", "A comfortable daypack for short hikes and day trips.", "https://example.test/items/8", {"capacity_liters": 20, "water_resistant": True}),
    (9, 1, "book", "The Art of Clear Thinking", "A practical guide to reasoning and decision-making.", "https://example.test/items/9", {"format": "hardcover", "language": "English"}),
    (10, 2, "product", "Wireless Noise-Cancelling Headphones", "Over-ear headphones for focused work and travel.", "https://example.test/items/10", {"wireless": True, "noise_cancelling": True}),
)


def initialize_demo_database(database_path: str) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT OR IGNORE INTO categories (category_id, parent_category_id, name, slug, description) VALUES (?, ?, ?, ?, ?)",
            CATEGORIES,
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO items
                (item_id, category_id, item_type, title, description, item_url, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (*item[:6], json.dumps(item[6]))
                for item in ITEMS
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO users
                (user_id, username, email, display_name, password_hash, is_active)
            VALUES (?, ?, ?, ?, '', 0)
            """,
            [
                (user_id, f"demo_graph_user_{user_id}", f"demo{user_id}@example.invalid", f"Demo profile {user_id}")
                for user_id in range(1, 6)
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO interactions (user_id, item_id, interaction_type, strength)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, 1, "view", 1.0), (1, 2, "click", 2.0), (1, 4, "like", 3.0),
                (2, 8, "view", 1.0), (2, 7, "purchase", 5.0), (2, 10, "click", 2.0),
                (3, 9, "like", 3.0), (3, 3, "purchase", 5.0), (3, 1, "click", 2.0),
                (4, 5, "view", 1.0), (4, 6, "purchase", 5.0), (4, 10, "like", 3.0),
                (5, 7, "click", 2.0), (5, 9, "view", 1.0), (5, 2, "share", 3.0),
            ],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO ratings (user_id, item_id, rating) VALUES (?, ?, ?)",
            [
                (1, 1, 5), (1, 2, 4), (2, 8, 5), (2, 7, 4), (3, 9, 5),
                (3, 3, 4), (4, 5, 5), (4, 6, 5), (5, 7, 5), (5, 2, 4),
            ],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO user_interests (user_id, category_id, interest_weight) VALUES (?, ?, ?)",
            [
                (1, 5, 0.95), (1, 6, 0.7), (1, 2, 0.65),
                (2, 4, 0.9), (2, 3, 0.55), (2, 2, 0.6),
                (3, 1, 0.85), (3, 5, 0.75), (3, 3, 0.5),
                (4, 6, 0.9), (4, 2, 0.7), (4, 4, 0.55),
                (5, 3, 0.9), (5, 1, 0.65), (5, 5, 0.6),
            ],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
