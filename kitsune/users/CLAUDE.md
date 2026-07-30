# users — profiles, auth, accounts

User `Profile`s, authentication, and account lifecycle.

- **Auth is OIDC via Mozilla accounts (FxA)** — `SumoOIDCAuthBackend` in `auth.py` (extends `mozilla_django_oidc`). Routes in `urls_oidc.py`: FxA authenticate / callback / logout, plus a **server-to-server webhook** at `fxa/events` (`WebhookView`) that receives account events (e.g. password change, deletion).
- `AccountEvent` records those webhook events; `EmailChange` / `Deactivation` cover account-lifecycle flows.
- The users API supports **both v1 and v2**.
- **Group visibility:** `Profile.visible_group_profiles(viewer)` lives here, but the *rule* (never `user.groups.all()`) is a cross-cutting invariant — see root `CLAUDE.md` → Security.
- Keep OIDC / FxA client ids, secrets, and endpoints in settings / env — never in code or here.
