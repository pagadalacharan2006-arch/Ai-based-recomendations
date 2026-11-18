from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import mysql.connector

from backend.config import build_config
from backend.routes.api import api


def create_app() -> Flask:
    config = build_config()
    app = Flask(__name__, static_folder=None)
    app.config.update(config)
    app.register_blueprint(api)

    @app.get("/")
    def index():
        return send_from_directory(app.config["FRONTEND_PUBLIC"], "index.html")

    @app.get("/src/<path:filename>")
    def frontend_source(filename: str):
        return send_from_directory(app.config["FRONTEND_SOURCE"], filename)

    @app.errorhandler(mysql.connector.Error)
    def database_error(error):
        app.logger.exception("MySQL request failed")
        return (
            jsonify(
                {
                    "error": "The database request failed. Check MySQL, the DB_* settings in .env, and apply the password-hash migration if this database predates account authentication."
                }
            ),
            503,
        )

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return error

    return app
