# questions — Q&A and AAQ

Support questions & answers, including the **Ask A Question (AAQ)** flow.

- **AAQ is a multi-step flow:** `views.aaq` / `aaq_step2` / `aaq_step3` (see `urls.py`), gated per product by support config (`Topic.in_aaq`, `has_support_config`).
- **Auto-tagging:** `question.auto_tag()` runs on question create *and* update — tags are derived, not only manual.
- Answers, votes, and solutions hang off `Question`; questions are indexed for search (see the `search` guide).
