import argparse
from getpass import getpass

from werkzeug.security import generate_password_hash

from backend.app import create_app
from backend.database import execute, fetch_one


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set or reset a local Weave account password."
    )
    parser.add_argument("identifier", help="Existing account username or email")
    args = parser.parse_args()

    password = getpass("New password (12–128 characters): ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 12 or len(password) > 128:
        parser.error("password must be between 12 and 128 characters")
    if password != confirmation:
        parser.error("passwords do not match")

    app = create_app()
    with app.app_context():
        account = fetch_one(
            "SELECT user_id FROM users WHERE username = %s OR email = %s LIMIT 1",
            (args.identifier, args.identifier),
        )
        if account is None:
            parser.error("no account was found for that username or email")
        execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (generate_password_hash(password), account["user_id"]),
        )

    print("Password updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
