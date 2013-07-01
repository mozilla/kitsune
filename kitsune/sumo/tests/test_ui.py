# -*- coding: utf-8 -*-
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import SeleniumTestCase

from nose.tools import eq_


class TestLanguageSwitch(SeleniumTestCase):

    def test_english_to_spanish(self):
        url = self.live_server_url + reverse('home', locale='en-US')
        self.webdriver.get(url)

        picker = self.webdriver.find_element_by_css_selector('.locale-picker')
        eq_(picker.text.lower(), 'english')
        picker.click()

        self.webdriver.find_element_by_css_selector('a[lang="es"]').click()

        url = self.live_server_url + reverse('home', locale='es')
        eq_(self.webdriver.current_url, url)

        picker = self.webdriver.find_element_by_css_selector('.locale-picker')
        eq_(picker.text.lower(), u'español')
