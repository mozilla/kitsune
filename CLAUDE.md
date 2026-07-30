# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

**Kitsune** is the Django platform behind SuMo (support.mozilla.org). Development is Docker-based.

This file holds **cross-cutting, non-obvious** knowledge. Discoverable detail is intentionally *not* duplicated here — read the source of truth instead:
- Commands → `Makefile` · services → `docker-compose.yml` · env vars → `.env-dist` · frontend build → `package.json` · dev scripts → `bin/`.
- **Versions** (Python, Django, Elasticsearch, …) → `pyproject.toml` and `package.json`. Don't hardcode version numbers in docs — they drift.
- **App-specific guidance** lives in per-app `CLAUDE.md` files (see *Per-app guides*); they load on demand when you work in that app.

## Stack (orientation — versions live in pyproject.toml / package.json)

Django + Python · PostgreSQL · Elasticsearch · Redis (cache + Celery broker) · Webpack / SCSS / vanilla JS + jQuery · uv (Python packaging) · ruff (lint + format) · Django TestCase + Playwright (E2E).

## App map

**Primary:** `wiki` (KB articles) · `questions` (Q&A / AAQ) · `forums` · `users` (profiles, auth) · `search` (Elasticsearch) · `gallery` (media) · `products` (products & topics) · `kpi` (metrics).
**Supporting:** `sumo` (core: `ModelBase`, base templates, middleware, jinja helpers) · `customercare` (Zendesk) · `flagit` (moderation) · `inproduct` (Firefox in-product redirects) · `llm` (AI: moderation / categorization / translation) · `messages` · `notifications` · `tidings` (email subscriptions) · `kbadge` · `groups` · `dashboards`.

## Conventions

- **Models** inherit `kitsune.sumo.models.ModelBase`. Use `LocaleField` for locale fields. Celery tasks in `tasks.py`; REST in `api.py`; routes in `urls.py` / `urls_api.py`.
- **Imports at the top of the file, always** — the only exception is breaking a genuine circular import, with a one-line note naming the cycle. Applies to test files too.
- **No environment-specific IDs** in code, comments, or migrations — DB primary keys differ per environment. Reference rows by slug / name.
- **Test factories** live in each app's `tests/__init__.py` (e.g. `kitsune/questions/tests/__init__.py`) — there are no `factories.py` files.
- **All user-facing strings** are translated with `_()` / `_lazy()`.
- Templating is **Django-Jinja** (not stock Django templates); helpers in `kitsune.sumo.templatetags.jinja_helpers`; mobile via the `mobile_template()` decorator.
- **Cache / Celery** run on Redis; use app-specific cache-key prefixes.

## Manager-method naming

Prefer concise, verb-based names that read naturally when chained — `GroupProfile.objects.visible(user)`, `Article.objects.active()`. Use a more verbose descriptive name only when concision would be unclear.

## Routing

i18n URL patterns. KB `/kb/` · questions `/questions/` · forums `/forums/` · gallery `/gallery/` · groups `/groups/`; users / products at root (`/users/`, `/firefox/`). APIs: v1 `/api/1/{app}/` (legacy), v2 `/api/2/{app}/` (current); GraphQL at `/graphql`. In-product integration under `/1/` (see the `inproduct` guide). Feature-flag JS at `/wafflejs`.

## Frontend

Webpack entrypoints are referenced by **name** from Jinja templates (`base.html` includes `entrypoints/{name}.html`). When removing an entry from `webpack/entrypoints.js`, grep templates for its name (`grep -rn '<name>' kitsune --include='*.html'`) and remove every reference — a missed one fails the build with `TemplateNotFound`.

## Security — GroupProfile visibility (CRITICAL)

`GroupProfile` has three visibility levels (PUBLIC, PRIVATE, MODERATED). Django's `User.groups` returns **all** groups, ignoring visibility — so bypassing the visibility layer leaks PRIVATE group membership into profiles, search indexing, and API responses.

**Never:**
```python
user.groups.all()                     # leaks PRIVATE groups
profile.user.groups.all()             # leaks PRIVATE groups
Group.objects.filter(user=some_user)  # bypasses visibility
```
**Always** use the visibility-aware paths:
```python
profile.visible_group_profiles(viewer=request.user)
GroupProfile.objects.visible(viewer).filter(group__user=some_user)
group_profile.can_view(request.user)
```
This applies equally in views, templates, API serializers, and search indexing.

## Testing

- Run tests **through Docker**, not `uv run`: targeted — `docker compose run --rm web ./manage.py test <dotted.path> --keepdb -v 2`; full suite — `make test`.
- Factories from `factory_boy` (in `tests/__init__.py`). Mock Elasticsearch on code paths that don't need a live index. E2E in `playwright_tests/`. Tests run with `TESTING=True`.
- Elasticsearch round-trip and index tests have real gotchas — see the `search` guide.

## Development practices

- Format with `ruff format`; lint with `ruff check`; run `make lint` (pre-commit) before committing.
- Be **specific with exception types** — catch `Model.DoesNotExist`, `KeyError`, etc., not bare `Exception`, so unexpected errors still surface.
- **Preserve functional parity** in dependency upgrades and cleanups — don't drop features to shrink a diff; a dropped feature is a regression.
- **No AI-planning references in code** — never leave `# per Plan 3`, step numbers, or ticket-scaffolding comments. An issue/PR reference that captures a real *why* is fine.
- This repo targets **Python 3.14** (ruff `target-version = py314`). Note `except A, B:` (unparenthesized multi-exception) is valid 3.14 syntax — don't flag it as an error.
- Don't add trailing whitespace or trailing blank lines at end of files.
- **`.env` gotcha:** `bin/dc_ci.sh` (and `.env-build`) overwrite `.env` — back up any local `.env` before running CI setup scripts.

## Localization

100+ locales. Locale definitions in `kitsune/lib/sumo_locales.py`; translations in `locale/`; per-language ES synonyms in `kitsune/search/dictionaries/synonyms/`.

## Per-app guides (load on demand)

Deeper, app-specific notes live in `kitsune/<app>/CLAUDE.md` and load only when you work in that app: **search**, **wiki**, **llm**, **retrieval**, **questions**, **users**, **customercare**, **inproduct**.
