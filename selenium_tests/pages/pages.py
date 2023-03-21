from selenium.webdriver.remote.webdriver import WebDriver

from selenium_tests.pages.contribute_page import ContributePage
from selenium_tests.pages.footer import FooterSection
from selenium_tests.pages.homepage import Homepage
from selenium_tests.pages.top_navbar import TopNavbar


class Pages:

    def __init__(self, driver: WebDriver):
        self.contribute_page = ContributePage(driver)
        self.homepage = Homepage(driver)
        self.footer_section = FooterSection(driver)
        self.top_navbar = TopNavbar(driver)
