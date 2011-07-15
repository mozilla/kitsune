import sys
import os
from nose.plugins.skip import SkipTest
from nose.plugins.multiprocess import MultiProcess
from nose.plugins.plugintest import munge_nose_output_for_doctest

_multiprocess_can_split_ = True

def setup_module():
    try:
        import multiprocessing
        if 'active' in MultiProcess.status:
            raise SkipTest("Multiprocess plugin is active. Skipping tests of "
                           "plugin itself.")
    except ImportError:
        raise SkipTest("multiprocessing module not available")



