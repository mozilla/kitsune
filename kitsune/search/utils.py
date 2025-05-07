from decouple import Csv, config

from django.conf import settings

from elasticsearch7 import Elasticsearch as ES7
from elasticsearch8 import Elasticsearch as ES8

from kitsune.lib.sumo_locales import LOCALES

# Module-level cache for ES version
_ES_VERSION = None


def locale_or_default(locale):
    """Return `locale` or, if `locale` isn't a known locale, a default.

    Default is taken from Django's LANGUAGE_CODE setting.

    """
    if locale not in LOCALES:
        locale = settings.LANGUAGE_CODE
    return locale


def get_es_version():
    """Get the Elasticsearch version, with caching to avoid repeated connections."""
    global _ES_VERSION

    # Return cached version if we've already determined it
    if _ES_VERSION is not None:
        return _ES_VERSION

    # Configure connection settings
    es_kwargs = {
        "hosts": config("ES_URLS", cast=Csv(), default="http://elasticsearch:9200"),
        "timeout": config("ES_TIMEOUT", default=5),
        "retry_on_timeout": config("ES_RETRY_ON_TIMEOUT", default=True, cast=bool),
        "use_ssl": config("ES_USE_SSL", default=False, cast=bool),
        "verify_certs": config("ES_VERIFY_CERTS", default=False, cast=bool),
    }

    # Add HTTP auth if provided
    http_auth = config("ES_HTTP_AUTH", default="", cast=Csv())
    if http_auth and len(http_auth) == 2:
        es_kwargs["http_auth"] = tuple(http_auth)

    # Add cloud ID if provided
    cloud_id = config("ES_CLOUD_ID", default="")
    if cloud_id:
        es_kwargs.pop("hosts", None)
        es_kwargs["cloud_id"] = cloud_id

    try:
        es = ES7(**es_kwargs)
        response = es.info()
        # Extract major version as integer
        _ES_VERSION = int(response["version"]["number"].split(".")[0])
    except Exception:
        try:
            es = ES8(**es_kwargs)
            response = es.info()
            # Extract major version as integer
            _ES_VERSION = int(response["version"]["number"].split(".")[0])
        except Exception as e:
            print(f"Elasticsearch connection error: {e}")
            _ES_VERSION = 0  # Default if connection fails

    return _ES_VERSION
