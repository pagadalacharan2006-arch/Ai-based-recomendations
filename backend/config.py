import os
import secrets
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def build_config() -> dict:
    demo_mode = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
    return {
        "HOST": os.getenv("FLASK_HOST", "127.0.0.1"),
        "PORT": int(os.getenv("FLASK_PORT", "5000")),
        "SECRET_KEY": os.getenv("APP_SECRET_KEY") or secrets.token_hex(32),
        "DB_DRIVER": "sqlite" if demo_mode else "mysql",
        "SQLITE_PATH": os.getenv(
            "SQLITE_PATH", str(PROJECT_ROOT / "demo.sqlite3")
        ),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": os.getenv("SESSION_COOKIE_SECURE", "false").lower()
        in {"1", "true", "yes"},
        "PERMANENT_SESSION_LIFETIME": timedelta(days=14),
        "MAX_CONTENT_LENGTH": 1024 * 1024,
        "MYSQL_CONFIG": {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "ai_graph_recommendation"),
            "connection_timeout": 5,
            "autocommit": False,
        },
        "FRONTEND_PUBLIC": PROJECT_ROOT / "frontend" / "public",
        "FRONTEND_SOURCE": PROJECT_ROOT / "frontend" / "src",
    }
