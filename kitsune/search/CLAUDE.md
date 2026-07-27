# search — Elasticsearch integration

ES-backed search. Custom document classes in `documents.py`; base machinery (`SumoDocument`, alias versioning) in `base.py`.

- **Index lifecycle:** `python manage.py es_init --migrate-writes --migrate-reads` to (re)initialize; `es_reindex` to reindex. Both are management commands in `search/management/commands/`.
- **Alias versioning:** `SumoDocument` manages read/write aliases (`migrate_writes` → new versioned index; `migrate_reads` → atomic read swap). Every question/wiki/forum document inherits this — treat `base.py` as high-blast-radius shared code.
- **Per-language synonyms** in `dictionaries/synonyms/`.

## Testing gotchas

- **`TEST=True` is required for index→search round-trip tests.** Ad-hoc `docker compose run` does not source `bin/test-env.sh`, so `settings.TEST` defaults False; ES then honors the 60s `refresh_interval` and just-written docs stay invisible → tests assert count 0. For those tests: `docker compose run --rm -e TEST=True web ./manage.py test <path> --keepdb`. The real runner (`bin/run-unit-tests.sh`) sets it for you.
- **The `--tag es` suite fails pre-existingly when run ad-hoc** — many `version_conflict_engine_exception` errors on `delete_by_query` in teardown, because ad-hoc runs skip the `es_init` setup the CI harness performs. Don't expect all-green. Regression-check ES-infra changes by **baseline diff** (`git stash` your change, run the same targeted tests, compare the failure profile), not absolute pass/fail.
