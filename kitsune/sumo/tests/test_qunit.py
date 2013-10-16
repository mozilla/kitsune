import re
from urllib2 import URLError

from kitsune.sumo.tests import SeleniumTestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# tl;dr: translate qunit test results into nose test results.
#
# Nose supports tests generators. These are functions that when run
# yield a series of tuples. The first member of each tuple is a function
# to call, and the rest are the arguments to pass to it. In this way you
# can have several related tests that can run, pass, and fail
# seperately. This is really cool.
#
# Sadly, they do not work if you are a subclass of TestCase. This is not
# cool. In particular, the below code relies on the setUp, setUpClass,
# and tearDownClass methods of SeleniumTestCase.
#
# In order to combine these two concepts, a dummy class is created which
# doesn't run any tests. Then a Nose test function runs the appropriate
# setup and teardown methods on the dummy test case, and yields a test
# for every test that Qunit lists.


class TestQunit(SeleniumTestCase):
    """This is the dummy test to get at the methods needed."""

    def runTest(self):
        """This dummy TestCase should run no tests."""
        pass


qunit_case = TestQunit()


def test_qunit():
    """Qunit tests."""
    # This yields functions that act as if they were methods in TestQunit.

    qunit_case.setUpClass()
    qunit_case.setUp()

    def t(elem):
        title = elem.find_element(By.XPATH, '../../strong').text
        title = re.sub(r' \(\d+, \d+, \d+\)$', '', title)
        state = elem.get_attribute('class')
        expects = elem.find_elements(By.CSS_SELECTOR, '.test-expected pre')
        actuals = elem.find_elements(By.CSS_SELECTOR, '.test-actual pre')

        actual = actuals[0].text if len(actuals) else None
        expect = expects[0].text if len(expects) else None

        msg = 'QUnit failure in "%s": %s != %s' % (title, expect, actual)
        assert state == 'pass', msg

    # Navigate to the qunit page.
    url = qunit_case.live_server_url + '/en-US/qunit'
    qunit_case.webdriver.get(url)

    # Get all the test rows
    selector = '#qunit-tests [id^=test-output] '
    selector = '{0} .fail, {0} .pass'.format(selector)
    selector = (By.CSS_SELECTOR, selector)

    qunit_case.webdriver.get_screenshot_as_file('/tmp/qunit.png')

    # Wait up to 30 seconds until the tests are done running.
    (WebDriverWait(qunit_case.webdriver, 30)
        .until(EC.text_to_be_present_in_element(
               (By.CSS_SELECTOR, '#qunit-testresult'), 'Tests completed')))

    # Get test results.
    test_elems = (WebDriverWait(qunit_case.webdriver, 30)
                  .until(EC.presence_of_all_elements_located(selector)))

    # Check everything
    for elem in test_elems:
        yield (t, elem)

    def qunit_cleanup():
        """Try to shutdown selenium. If it fails, don't fail the tests."""
        try:
            qunit_case.tearDown()
            qunit_case.tearDownClass()
        except URLError:
            pass

    yield (qunit_cleanup, )
