# search — Elasticsearch integration

ES-backed search. Custom document classes in `documents.py`; base machinery (`SumoDocument`, alias versioning) in `base.py`.

- **Index lifecycle:** `python manage.py es_init --migrate-writes --migrate-reads` to (re)initialize; `es_reindex` to reindex. Both are management commands in `search/management/commands/`.
- **Alias versioning:** `SumoDocument` manages read/write aliases (`migrate_writes` → new versioned index; `migrate_reads` → atomic read swap). Every question/wiki/forum document inherits this — treat `base.py` as high-blast-radius shared code.
- **Per-language synonyms** in `dictionaries/synonyms/`.

## Testing gotchas

- **`TEST=True` is required for index→search round-trip tests.** Ad-hoc `docker compose run` does not source `bin/test-env.sh`, so `settings.TEST` defaults False; ES then honors the 60s `refresh_interval` and just-written docs stay invisible → tests assert count 0. For those tests: `docker compose run --rm -e TEST=True web ./manage.py test <path> --keepdb`. The real runner (`bin/run-unit-tests.sh`) sets it for you.
- **Test indices are fixture-owned.** `ElasticTestCase` initializes lexical indices once per process, including serial runs; don't pre-run `es_init` for tests. Parallel workers bind document indices and aliases to run- and worker-specific prefixes before Django setup. Retrieval chunk generations remain owned by `ChunkIndexTestCase`.
- **Keep ES assertions index-scoped.** Cluster-wide counters include other workers' activity. Use the test's physical index for statistics and keep temporary indices under `settings.ES_INDEX_PREFIX` so run-owned cleanup includes them.
