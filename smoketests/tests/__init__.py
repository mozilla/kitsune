import time


class TestCase(object):
    def take_a_breather(self):
        """Sleeps for a second so as to reduce sporadic test failures"""
        time.sleep(1)
