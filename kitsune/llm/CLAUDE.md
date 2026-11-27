# llm — AI features

LLM-backed features: content moderation / categorization, spam detection, l10n / translation, and support flows. Subpackages: `categorization/`, `spam/`, `l10n/`, `support/`.

- **Model access goes through the factory `get_llm(...)` in `utils.py`** — don't instantiate provider clients directly. Model choice is config-driven (currently Vertex AI Gemini via LangChain).
- Prompts live in `prompt.py`; batch / async work in `tasks.py`.
- Keep provider specifics (project, model id, credentials) in settings / env — never hardcode them here.

## `l10n/ui_labels/` — official translations of UI labels

Finds the official translation of each `{menu}`, `{button}` and `{pref}` label in a KB article, from the products' own l10n repos, and writes it into machine translations when the waffle switch `official-ui-labels` is on.

- **Start with the package docstring** (`l10n/ui_labels/__init__.py`). It gives the big picture and defines the words the code uses: label, use, position, official label, owner, string, source, catalog, spot.
- **Layout.** `strings/` reads the products' strings from GitHub and looks them up. `owners/` holds the list of owners, and `owners/lookup.py` finds each label's owner by asking an LLM whose screen it is on. `official.py` chooses a label's official label, `pairing.py` matches translated labels to English ones, and `translation.py` and `report.py` use all of that.
- **Prompts.** The owner prompt is in `owners/prompt.py`. The pairing prompt is short and sits in `pairing.py`, next to the code that reads its answer. The label rules of the translation prompt are in `l10n/prompt.py`.
- **Strings are synced once a day** from GitHub. The `sync_ui_strings` task starts one `sync_ui_string_source` task per source, and `build_ui_spot_lists` runs an hour later. A source that borrows brand names from another one is read again the day after that one changes.
- **To add an owner**, add it to `owners/__init__.py`, its files to `strings/sources.py`, and its list of shipped locales to `strings/shipped_locales.py`.
- **Strings and LLM answers are saved and reused.** After changing a parser, raise `PARSER_VERSION` in `strings/sync.py`. After changing a question, raise `QUESTION_VERSION` in `owners/prompt.py` or `pairing.py`. Otherwise the old strings or answers stay in use.
- **`./manage.py ui_labels report`** compares translated labels with the official labels. It changes no article, but it asks the LLM about every owner and pair that isn't saved yet.
- **Machine translation** (`translation.py`, used by `l10n/translator.py`) tells the LLM the official labels and checks its answer.
- **Tests never call GitHub or an LLM.** Patch `strings.github` functions, and `get_llm` in `owners.lookup`, `pairing` and `translator`, with stand-ins. Tests that reach `get_owners` also patch `owners.lookup.redis_client`, so they take no real lock. A test that opens an admin page logs in with `login_to_admin` from `kitsune.sumo.tests`, because outside `DEV` mode the admin only accepts an OIDC session.
