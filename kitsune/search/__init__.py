from django.utils.translation import gettext_lazy as _lazy

# Import early to set up module aliases for elasticsearch and elasticsearch_dsl
from kitsune.search.es_compat import setup_elasticsearch_modules

# Make sure the module aliases are set up
setup_elasticsearch_modules()

WHERE_WIKI = 1
WHERE_SUPPORT = 2
WHERE_BASIC = WHERE_WIKI | WHERE_SUPPORT
WHERE_DISCUSSION = 4

HIGHLIGHT_TAG = "strong"
SNIPPET_LENGTH = 500

NO_MATCH = _lazy("No pages matched the search criteria")
