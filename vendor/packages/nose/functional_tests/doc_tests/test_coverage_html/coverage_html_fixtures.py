import sys
import os
import shutil
from nose.plugins.skip import SkipTest
from nose.plugins.cover import Coverage
from nose.plugins.plugintest import munge_nose_output_for_doctest

# This fixture is not reentrant because we have to cleanup the files that
# coverage produces once all tests have finished running.
_multiprocess_shared_ = True

def setup_module():
    try:
        import coverage
        if 'active' in Coverage.status:
            raise SkipTest("Coverage plugin is active. Skipping tests of "
                           "plugin itself.")
    except ImportError:
        raise SkipTest("coverage module not available")

def teardown_module():
    # Clean up the files produced by coverage
    cover_html_dir = os.path.join(os.path.dirname(__file__), 'support', 'cover')
    if os.path.exists(cover_html_dir):
        shutil.rmtree(cover_html_dir)

