# wiki — Knowledge Base

KB articles (`Document`) with revisions, translations, and wiki-markup rendering.

- **Parser:** `parser.py` renders wiki markup → HTML. `wiki_to_html()` is the entry point; `WikiParser.expand_fors()` renders `{for platform,version}` show-for blocks as `<div|span class="for" data-for="...">`, stored on `Document.html`. Show-for scope is subtle — a section can be conditional on platform / version / product.
- **Translations:** an article and its localized versions form a family. `Document.parent_id` links a translation to its English parent; `Document.translated_to(locale)` resolves a locale variant.
- **Currency:** `Document.is_outdated(level)` compares a translation against its parent's significant revisions (MEDIUM / MAJOR) — a translation can be stale without being wrong.
- Rendering must be **faithful** — don't "clean up" parser output (e.g. spacing around punctuation); it corrupts locale typography.
