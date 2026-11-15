# Django RBAC

A simple role-based access control project built with Django and Django REST Framework.

## Install

Requires uv. The Python version is defined in `pyproject.toml`. Run from the repository root:

```sh
uv sync --extra dev
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
uv run --extra dev pytest --ds=config.settings --override-ini="addopts="
```

The test suite is under development. This command overrides the outdated settings and coverage defaults.

## Thanks

Thanks to [AI Hero — Skills Teach](https://www.aihero.dev/skills-teach) for helping me understand the concept.
