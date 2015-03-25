from kitsune.sumo.tests import SeleniumTestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nose.tools import eq_


class TestQunit(SeleniumTestCase):
    def test_qunit(self):
        """Runs all the Qunit tests."""
        # Navigate to the qunit page.
        url = self.live_server_url + '/en-US/qunit'
        self.webdriver.get(url)

        # Wait up to 30 seconds until the tests are done running.
        (WebDriverWait(self.webdriver, 30)
            .until(EC.text_to_be_present_in_element(
                   (By.CSS_SELECTOR, '#qunit-testresult'), 'Tests completed')))

        self.webdriver.get_screenshot_as_file('/tmp/qunit.png')

        # Get test results.
        selector = '#qunit-tests > li.pass, #qunit-tests > li.fail'
        test_groups = self.webdriver.find_elements(By.CSS_SELECTOR, selector)
        total_fails = 0

        # Print number of test groups so it's more likely we notice problems
        # with this test.
        print 'QUNIT: examining %d test groups...' % len(test_groups)

        # Go through each test group to see status.
        for group in test_groups:
            state = group.get_attribute('class')

            # If the whole group passed, we don't need to check
            # individual tests, so we can move on.
            if state == 'pass':
                continue

            # Suite didn't pass, so we check individual tests in the group and
            # print out a message for each failure.
            total_fails += 1
            title = group.find_element(By.CSS_SELECTOR, '.test-name').text
            tests = group.find_elements(By.CSS_SELECTOR, '.pass, .fail')
            for test_elem in tests:
                state = test_elem.get_attribute('class')
                if state == 'pass':
                    continue

                expects = test_elem.find_elements(By.CSS_SELECTOR, '.test-expected pre')
                actuals = test_elem.find_elements(By.CSS_SELECTOR, '.test-actual pre')

                actual = actuals[0].text if len(actuals) else None
                expect = expects[0].text if len(expects) else None

                print 'QUNIT FAIL: in "%s": %s != %s' % (title, expect, actual)

        # Assert we had no failures in the tests.
        eq_(total_fails, 0, 'One or more Qunit tests failed; see output for details')
