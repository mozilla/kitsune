# customercare — Zendesk integration

Bridges support tickets to **Zendesk**.

- **All Zendesk API access goes through `ZendeskClient` in `zendesk.py`** — don't call the API elsewhere.
- `SupportTicket` (`models.py`) mirrors Zendesk state. Sync semantics live on the model: `syncable` / `is_syncable` (whether a ticket should push) and `status_label` (maps Zendesk status). Sync is signal-driven (`signals.py`) with Celery tasks in `tasks.py`.
- Keep the Zendesk subdomain, credentials, and tokens in settings / env — never here.
