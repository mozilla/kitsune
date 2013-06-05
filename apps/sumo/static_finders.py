from django.contrib.staticfiles.finders import BaseStorageFinder
from django.contrib.staticfiles.storage import StaticFilesStorage


class WTFinder(BaseStorageFinder):
    """A staticfiles finder that looks in STATIC_ROOT."""
    storage = StaticFilesStorage

    def list(self, ignore_patterns):
        return []
