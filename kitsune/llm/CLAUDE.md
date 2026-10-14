# llm — AI features

LLM-backed features: content moderation / categorization, spam detection, l10n / translation, and support flows. Subpackages: `categorization/`, `spam/`, `l10n/`, `support/`.

- **Provider access stays centralized in `utils.py`**: classification uses `evaluate_decisions(...)`; advisory assessment, generation, and translation use `get_llm(...)`. Don't instantiate provider clients in classifiers. Classification model, credentials, endpoint, timeout, and probability cutoffs come from Django settings / env.
- Prompts live in `prompt.py`; batch / async work in `tasks.py`.
- Keep provider specifics (project, model id, credentials) in settings / env — never hardcode them here.
