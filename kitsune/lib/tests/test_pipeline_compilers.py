from kitsune.lib.pipeline_compilers import BrowserifyCompiler
from kitsune.sumo.tests import TestCase


class TestBrowserifyCompiler(TestCase):
    def setUp(self):
        self.compiler = BrowserifyCompiler(False, None)

    def test_matches_files_no_hash(self):
        assert self.compiler.match_file("community-l10n.browserify.js")

    def test_matches_files_hash(self):
        assert self.compiler.match_file("community-l10n.browserify.e6d41cfdc0d1.js")

    def test_doesnt_match_non_browserify_no_hash(self):
        assert not self.compiler.match_file("community-l10n.js")

    def test_doesnt_match_non_browserify_hash(self):
        assert not self.compiler.match_file("community-l10n.e6d41cfdc0d1.js")
