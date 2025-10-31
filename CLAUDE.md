# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment Setup

This is **Kitsune**, the Django platform that powers SuMo (support.mozilla.org). The project uses Docker for development.

### Quick Start Commands

```bash
# Initial setup (creates .env, builds images, installs dependencies)
make init                    # Run bootstrap script, migrations, node setup
make build                  # Build Docker images

# Run the application
make start                  # Start all services via docker-compose

# Development shells
make shell                  # Bash shell in container
make runshell              # Bash shell with ports bound
make djshell               # Django shell (ipython)
make dbshell               # PostgreSQL shell
```

### Testing Commands

```bash
# Python tests (via Docker - recommended)
make test                   # Run Django unit tests via ./bin/run-unit-tests.sh
make djshell               # Django shell for interactive testing

# Python tests (direct commands - Docker container only)
python manage.py test       # Direct Django test command (inside container)
python manage.py test path.to.specific.test --verbosity=2

# Python tests (with uv venv - local development)
uv run python manage.py test                              # Run all tests in uv environment
uv run python manage.py test path.to.specific.test       # Run specific test
uv run python manage.py test --verbosity=2 --keepdb      # Verbose output, keep test DB

# JavaScript tests
make test-js               # Run JS tests via npm run webpack:test

# Lint and format
make lint                  # Run pre-commit hooks (includes ruff)
ruff format                # Format Python code with ruff (recommended)
npm run stylelint          # Lint SCSS files
```

## Application Architecture

### Core Django Apps Structure

**Primary Applications:**
- `wiki/` - Knowledge Base articles and documentation
- `questions/` - Support questions and answers (Q&A system)
- `forums/` - Discussion forums
- `users/` - User profiles, authentication, and account management
- `search/` - Elasticsearch-powered search functionality
- `gallery/` - Media management (images, videos)
- `products/` - Mozilla product definitions and topics
- `kpi/` - Metrics and analytics dashboard

**Supporting Applications:**
- `sumo/` - Core utilities, base templates, middleware
- `flagit/` - Content moderation system
- `messages/` - Private messaging between users
- `notifications/` - Event notification system
- `tidings/` - Email notification subscription management
- `kbadge/` - Badge system for user achievements
- `groups/` - User group management
- `dashboards/` - Analytics and reporting dashboards
- `llm/` - AI/ML features (moderation, translations)

### Key Technologies

- **Backend:** Django 4.2+, Python 3.11
- **Package Management:** uv (replaced poetry in July 2025)
- **Database:** PostgreSQL
- **Search:** Elasticsearch 9.0+
- **Cache:** Redis
- **Task Queue:** Celery with Redis broker
- **Frontend:** Webpack, SCSS, vanilla JavaScript + jQuery
- **Testing:** Django TestCase, pytest for E2E (Playwright)
- **Linting:** ruff (replaced flake8/black in July 2025)

### Environment Variables

Essential environment variables are defined in `.env-dist`. Key ones include:
- `DATABASE_URL` - PostgreSQL connection
- `ES_URLS` - Elasticsearch endpoints
- `REDIS_*` - Redis configuration for cache and Celery
- `DEBUG`, `DEV` - Development mode flags

### Docker Services

The `docker-compose.yml` defines:
- `web` - Main Django application (port 8000)
- `postgres` - Database (port 5432)
- `elasticsearch` - Search engine (port 9200)
- `redis` - Cache and message broker
- `celery` - Background task worker
- `mailcatcher` - Email testing (port 1080)

### Package Management with uv

```bash
# Install dependencies
uv sync                    # Install all dependencies
uv sync --frozen           # Install from lockfile without updates
uv add package-name        # Add new dependency
uv pip install package     # Install package in current environment
```

### Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Elasticsearch Management

```bash
python manage.py es_init --migrate-writes --migrate-reads  # Initialize ES
python manage.py es_reindex --count 10 --verbosity 2       # Reindex content
```

### Localization (L10n)

Kitsune supports 100+ locales. Key files:
- `kitsune/lib/sumo_locales.py` - Locale definitions
- `locale/` - Translation files
- Language-specific synonyms in `search/dictionaries/synonyms/`

### Frontend Build System

```bash
# Webpack commands
npm run webpack:build      # Production build
npm run webpack:watch      # Development with file watching
npm run build:styleguide   # Generate CSS styleguide

# Browser development
npm run start             # Webpack + BrowserSync
npm run browser-sync      # Live reload server
```

### Common Development Patterns

- Models use `ModelBase` from sumo.models for common fields
- Views often use `mobile_template()` decorator for mobile templates
- Search uses custom Elasticsearch Document classes in `search/documents.py`
- All user-facing strings should be marked for translation with `_()` or `_lazy()`
- Cache keys use app-specific prefixes (defined in individual apps)

### Testing Guidelines

- Python tests live in `tests/` directories within each app
- Use factories from `factory_boy` for test data creation
- Search tests often need `@mock.patch` for Elasticsearch
- E2E tests use Playwright and are in `playwright_tests/`
- Tests run in isolated database with `TESTING=True`

### Key Configuration Files

- `pyproject.toml` - Python dependencies and ruff configuration
- `uv.lock` - Locked dependency versions (replaces poetry.lock)
- `package.json` - Node.js dependencies, build scripts
- `webpack.*.js` - Frontend build configuration
- `Makefile` - Development commands wrapper
- `docker-compose.yml` - Local development stack
- `.github/dependabot.yml` - Automated dependency updates for uv and npm

### URL Structure and Routing

Kitsune uses Django's i18n URL patterns with specific routing conventions:

**Primary URL Patterns:**
- Knowledge Base: `/kb/` (wiki articles)
- Search: `/search/`
- Forums: `/forums/`
- Questions: `/questions/` (Q&A system)
- Gallery: `/gallery/` (media)
- Groups: `/groups/`
- Users: Root level paths like `/users/`
- Products: Root level paths like `/firefox/`

**API Endpoints:**
- v1 APIs: `/api/1/{app}/` (legacy)
- v2 APIs: `/api/2/{app}/` (current)
- Mixed APIs: `/api/{app}/` (users API supports both versions)
- GraphQL: `/graphql` (with GraphiQL interface)

**Special Routes:**
- `/1/` - In-product integration endpoints
- `/wafflejs` - Feature flag JavaScript
- `contribute.json` - Mozilla contribution metadata

### Model Architecture Patterns

**Base Model Usage:**
- All models inherit from `kitsune.sumo.models.ModelBase`
- Provides common functionality: `objects_range()`, `update()` methods
- Use `LocaleField` for language/locale fields (max_length=7, uses LANGUAGE_CHOICES)
- Models define `updated_column_name` property for date range queries

**Common Model Patterns:**
- Use `factory_boy` factories for test data (located in each app)
- Celery tasks defined in `tasks.py` files within apps
- API endpoints follow REST conventions in `api.py` files
- Each app has dedicated `urls.py` and often `urls_api.py`

### Template System

**Template Architecture:**
- Uses Django-Jinja templating engine (not standard Django templates)
- Mobile-specific templates supported via `mobile_template()` decorator
- Template tags in `kitsune.sumo.templatetags.jinja_helpers`
- Localization: All user-facing strings use `_()` or `_lazy()` for translation

### Search Integration

**Elasticsearch Setup:**
- Version 9.0+ required
- Custom Document classes in `search/documents.py`
- Management commands for index operations:
  - `es_init --migrate-writes --migrate-reads` - Initialize
  - `es_reindex --count 10 --verbosity 2` - Reindex content
- Language-specific synonyms in `search/dictionaries/synonyms/`

### Cache and Performance

**Caching Strategy:**
- Redis-backed caching and session storage
- App-specific cache key prefixes (defined in individual apps)
- Celery uses Redis as message broker
- Cache configuration via `REDIS_*` environment variables

### Development Scripts

**Useful Scripts in `bin/`:**
- `run-unit-tests.sh` - Main test runner (used by `make test`)
- `run-web-bootstrap.sh` - Initial Django setup (migrations, collectstatic)
- `run-node-bootstrap.sh` - Node.js dependency installation
- `run-celery-worker.sh` - Background task worker
- `run-celery-beat.sh` - Scheduled task runner

### Development Best Practices

- Always format Python files after changes with `ruff format`
- Use `ruff check` for linting python files
- Run `make lint` before committing (uses pre-commit hooks)
- Use uv for Python package management
- Dependabot automatically updates dependencies weekly
- **Do not add trailing spaces at the end of files**
