from django.contrib.staticfiles.finders import BaseStorageFinder
from django.contrib.staticfiles.storage import StaticFilesStorage


class WTFinder(BaseStorageFinder):
    """A staticfiles finder that looks in STATIC_ROOT.

    This is super lame!

    It is specifically for when DEBUG = True because jingo-minify puts
    compiled files in STATIC_ROOT. gah!
    """
    storage = StaticFilesStorage

    def list(self, ignore_patterns):
        return []
