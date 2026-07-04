# AGENTS.md — AI Coding Agent Instructions

Purpose
- Provide minimal, actionable guidance so AI coding agents can be productive in this repository.

Quick start (developer)
- Create and activate a Python virtualenv (Windows PowerShell):
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`
- Run migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`
- Run development server: `python manage.py runserver`
- Run tests: `python manage.py test`

Project layout & conventions
- Django project root: `manage.py` and `config/` (settings at `config.settings`).
- Key apps: `accounts`, `medications`, `scheduling`, `notifications`, `reports`, `api`.
- App conventions: models in `models.py`, serializers in `serializers.py`, views in `views.py`, URL routes in `urls.py`, forms in `forms.py`, tests in `tests.py`.
- REST APIs use Django REST Framework (see `requirements.txt`). Use function-based `@api_view` endpoints in `medications.views` and `api.views`.

Environment notes
- `config/settings.py` currently uses PostgreSQL defaults (NAME: `medication_db`, USER: `postgres`, PASSWORD: in-file). Agents should NOT commit secrets; suggest using environment variables or `python-decouple`.
- Time zone: `Asia/Riyadh`, language: `ar-sa`.

What agents should do first
- Look for failing tests or lint errors before large edits.
- Prefer minimal, focused changes that preserve existing APIs and database migrations.
- When adding or changing models, create migrations and include migration files in commits.

Files worth checking before edits
- `requirements.txt` — dependency list
- `manage.py` and `config/settings.py` — run and configuration details
- App folders (e.g., `medications/`, `accounts/`) — follow local app patterns

If you modify project configuration or add new dependencies
- Update `requirements.txt` and mention installation steps in PR description.

Contact / next steps
- Ask maintainers for preferred CI, linting, or pre-commit hooks before adding them.
