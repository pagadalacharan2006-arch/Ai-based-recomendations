# Weave — AI-Based Recommendation System Using Graph Structures

Weave is a full-stack recommendation website backed by MySQL. Flask serves the API and native JavaScript modules, so there is no Node build step.

## Features

- Account registration, login, signed sessions, and CSRF-protected writes.
- A personalized recommendation dashboard, catalog search, categories, saved items, ratings, and weighted interests.
- Recommendation history and weighted graph-based scoring.
- A responsive interface for desktop and mobile.

The recommender combines weighted user-item interaction, rating, and saved-item edges; user similarity is estimated using weighted Jaccard overlap. The score also considers category interests, item popularity, and ratings.

## Windows setup

1. Start MySQL. For a fresh install, load `database.sql` into MySQL; it creates and seeds `ai_graph_recommendation`.
2. Copy `.env.example` to `.env` in the project root. Set `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` to match your local MySQL account. Generate a persistent session key with `python -c "import secrets; print(secrets.token_hex(32))"` and set it as `APP_SECRET_KEY`. Keep `.env` private; it is ignored by Git.
3. If upgrading a database created from the earlier version of `database.sql`, run [`migrations/001_add_user_password_hash.sql`](./migrations/001_add_user_password_hash.sql) **once** before starting the app. Existing non-sample accounts need a password set with the admin command below.
4. From PowerShell in the project root, install dependencies and start the site:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python run.py
   ```

5. Open <http://127.0.0.1:5000>, then register or sign in.

The five sample accounts use password `WeaveDemo!2026` (for example, username `maya_chen`). These are local demo credentials; change or remove them before deployment.

To set/reset an existing account password from PowerShell, run `python -m backend.set_password username-or-email`. The command prompts for the new password without echoing it.

For HTTPS deployment, set `SESSION_COOKIE_SECURE=true` and configure a strong persistent `APP_SECRET_KEY`. The app binds to `127.0.0.1` by default.

## API overview

- Public: `GET /api/health`, `GET /api/categories`, `GET /api/auth/csrf`
- Accounts: `GET /api/auth/me`, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`
- Authenticated: `GET /api/catalog`, `GET /api/dashboard`, `GET /api/history`
- Authenticated account data: saved items, ratings, interactions, and weighted interests under `/api/users/{id}/...`

Mutating API calls require the session CSRF token in the `X-CSRF-Token` header. The frontend handles this automatically.

## Tests

```powershell
python -m unittest discover -s tests -v
```
