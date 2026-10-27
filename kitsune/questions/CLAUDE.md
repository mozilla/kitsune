# questions — Q&A and AAQ

Support questions & answers, including the **Ask A Question (AAQ)** flow.

- **AAQ is a multi-step flow:** `views.aaq` / `aaq_step2` / `aaq_step3` (see `urls.py`); the support router (`products.routing.route_support`, surfaced as `sumo.utils.get_aaq_context`) picks each product's action (forum, product ticket, or enterprise ticket), and `Topic.in_aaq` its topics.
- **Auto-tagging:** `question.auto_tag()` runs on question create *and* update — tags are derived, not only manual.
- Answers, votes, and solutions hang off `Question`; questions are indexed for search (see the `search` guide).
