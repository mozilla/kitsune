from selenium.webdriver.common.by import By
from selenium_tests.core.base_page import BasePage


class ContributorForumPage(BasePage):
    __breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")
    __breadcrumb_homepage = (By.XPATH, "//ol[@id='breadcrumbs']/li[1]")
    __main_page_header = (By.XPATH, "//div[@id='forums']/h1[@class='sumo-page-heading']")
    __for_contributors_side_navbar_items = (By.XPATH, "//ul[@class='sidebar-nav--list']/li/a")
