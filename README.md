# Django RBAC

A simple role-based access control project built with Django and Django REST Framework.

## Install

Requires uv. The Python version is defined in `pyproject.toml`. Run from the repository root:

```sh
uv sync
```

## Run

```sh
uv run python manage.py migrate
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Seed demo data

```sh
uv run python manage.py seed
```

Runs migrations and replaces existing users, organizations, roles, and projects with demo data. Demo login: `superuser1` / `password123`.

## Tests (under development)

```sh
uv run pytest
```

The test suite is under development. pytest reads its settings from `pyproject.toml`.

## Format and lint

Run these commands from the repository root. isort sorts imports, Black formats code, and Flake8 checks for style issues and common mistakes:

```sh
uv run isort .
uv run black .
uv run flake8 .
```

Run isort before Black. Flake8 reads its settings from `pyproject.toml` using the `flake8-pyproject` plugin.

To check formatting and imports without changing files:

```sh
uv run isort --check-only .
uv run black --check .
```

## Thanks

Thanks to [AI Hero — Skills Teach](https://www.aihero.dev/skills-teach) for helping me understand the concept.
