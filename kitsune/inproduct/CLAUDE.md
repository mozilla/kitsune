# inproduct — Firefox in-product redirects

⚠️ **HIGH BLAST RADIUS — READ BEFORE CHANGING.**

This app translates redirect requests **originating from within shipped Firefox** into canonical support URLs. The URL contract is consumed by **released browsers in the wild** — breaking or changing it breaks in-product help for users who can't update. Treat the redirect behavior as a frozen external contract: any change must preserve existing `(product, version, platform, locale, topic)` → URL resolution.

- `Redirect` model (`models.py`) stores the mappings; `views.redirect(request, product, version, platform, locale, topic)` resolves them; request handling in `middleware.py`.
- Small app, but load-bearing for browser releases — add tests for any mapping change, and never remove a mapping without confirming no shipped Firefox depends on it.
