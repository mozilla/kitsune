# llm — AI features

LLM-backed features: content moderation / categorization, spam detection, l10n / translation, and support flows. Subpackages: `categorization/`, `spam/`, `l10n/`, `support/`.

- **Model access goes through the factory `get_llm(...)` in `utils.py`** — don't instantiate provider clients directly. Model choice is config-driven (currently Vertex AI Gemini via LangChain).
- Prompts live in `prompt.py`; batch / async work in `tasks.py`.
- Keep provider specifics (project, model id, credentials) in settings / env — never hardcode them here.
