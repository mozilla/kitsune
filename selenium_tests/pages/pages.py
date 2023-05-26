from selenium.webdriver.remote.webdriver import WebDriver

from selenium_tests.pages.contribute_pages.contribute_page import ContributePage
from selenium_tests.pages.contribute_pages.ways_to_contribute_pages import WaysToContributePages
from selenium_tests.pages.footer import FooterSection
from selenium_tests.pages.homepage import Homepage
from selenium_tests.pages.kb_article import KbArticle
from selenium_tests.pages.top_navbar import TopNavbar
from selenium_tests.pages.product_support_page import ProductSupportPage


class Pages:
    def __init__(self, driver: WebDriver):
        self.contribute_page = ContributePage(driver)
        self.homepage = Homepage(driver)
        self.footer_section = FooterSection(driver)
        self.top_navbar = TopNavbar(driver)
        self.kb_article = KbArticle(driver)
        self.product_support_page = ProductSupportPage(driver)
        self.ways_to_contribute_pages = WaysToContributePages(driver)
