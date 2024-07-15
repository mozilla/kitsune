from playwright_tests.core.testutilities import TestUtilities
import pytest
import allure
from pytest_check import check
from playwright.sync_api import expect

from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.messages.explore_help_articles.kb_translation_messages import (
    KbTranslationMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from kitsune.settings import SUMO_LANGUAGES, FALLBACK_LANGUAGES, NON_SUPPORTED_LOCALES


class TestArticleTranslation(TestUtilities, KbTranslationMessages):

    # C2489548, C2490043, C946153
    @pytest.mark.kbArticleTranslation
    def test_not_ready_for_localization_articles_dashboard_status(self):
        with allure.step("Signing in with an Admin account"):
            username = self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and approving it without marking it as "
                         "ready for localization"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )
            parent_article_url = self.get_page_url()

        with allure.step("Clicking on the Translate Article Editing Tools option and selecting "
                         "the ro locale"):
            self.sumo_pages.kb_article_page._click_on_translate_article_option()
            self.sumo_pages.translate_article_page._click_on_romanian_locale_from_list()
            translation_url = self.get_page_url()

        with check, allure.step("Verifying that the correct banner is displayed"):
            check.equal(
                (self.sumo_pages.translate_article_page
                 ._get_text_of_article_unready_for_translation_banner()),
                KBArticlePageMessages.KB_ARTICLE_NOT_READY_FOR_TRANSLATION_BANNER
            )

        with allure.step("Navigating to the localization dashboard and verifying that the "
                         "article is not listed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            expect(
                (self.sumo_pages.most_visited_translations_page
                 ._get_a_particular_article_title_locator(article_details['article_title']))
            ).to_be_hidden()

        with allure.step("Navigating to the localization unreviewed page and verifying that the "
                         "article is not listed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['localization_unreviewed']
            )
            expect(
                self.sumo_pages.localization_unreviewed_page._get_listed_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Navigating back to the translation page and performing a translation"):
            self.navigate_to_link(translation_url)
            translation = self.sumo_pages.submit_kb_translation_flow._add_article_translation(
                approve_translation_revision=False
            )

        with allure.step("Navigating to the localization dashboard and verifying that the "
                         "article is not listed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            expect(
                (self.sumo_pages.most_visited_translations_page
                 ._get_a_particular_article_title_locator(translation['translation_title']))
            ).to_be_hidden()

        with allure.step("Navigating to the localization unreviewed page and verifying that the "
                         "article is displayed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['localization_unreviewed']
            )
            expect(
                self.sumo_pages.localization_unreviewed_page._get_listed_article(
                    translation['translation_title']
                )
            ).to_be_visible()

        with check, allure.step("Verifying that the correct modified by text is displayed"):
            check.equal(
                self.sumo_pages.localization_unreviewed_page._get_modified_by_text(
                    translation['translation_title']
                ),
                super().get_unreviewed_localization_modified_by_text(username)
            )
        with allure.step("Clicking on the article approving the revision"):
            self.sumo_pages.localization_unreviewed_page._click_on_a_listed_article(
                translation['translation_title']
            )
            self.sumo_pages.submit_kb_translation_flow.approve_kb_translation(
                translation['revision_id']
            )

        with allure.step("Navigating to the localization unreviewed page and verifying that the "
                         "article is not displayed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            expect(
                self.sumo_pages.localization_unreviewed_page._get_listed_article(
                    translation['translation_title']
                )
            ).to_be_hidden()

        with check, allure.step("Navigating to the localization dashboard and verifying that the "
                                "article is not displayed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            expect(
                self.sumo_pages.localization_unreviewed_page._get_listed_article(
                    translation['translation_title']
                )
            ).to_be_hidden()

        with allure.step("Navigating to the parent article and marking it as ready for l10n"):
            self.navigate_to_link(parent_article_url)
            self.sumo_pages.kb_article_show_history_page._click_on_ready_for_l10n_option(
                article_details['first_revision_id']
            )
            self.sumo_pages.kb_article_show_history_page._click_on_submit_l10n_readiness_button()

        with check, allure.step("Navigating to the localization dashboard and verifying that the "
                                "article is displayed with the correct status"):
            self.wait_for_given_timeout(2000)
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            check.equal(
                self.sumo_pages.most_visited_translations_page._get_updated_localization_status(
                    translation['translation_title']
                ),
                super().LOCALIZATION_DASHBOARD_TRANSLATED_STATUS
            )

        with allure.step("Deleting the parent article"):
            self.navigate_to_link(parent_article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

        with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                                "that the 404 page is returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    translation_url
                )
            response = navigation_info.value
            assert response.status == 404

    # C2489548
    @pytest.mark.kbArticleTranslation
    def test_ready_for_localization_articles_dashboard_status(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and marking it as ready for localization"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True, ready_for_localization=True
            )
            parent_article_url = self.get_page_url()

        with check, allure.step("Navigating to the localization dashboard and verifying that the "
                                "correct status is displayed"):
            self.wait_for_given_timeout(2000)
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            check.equal(
                (self.sumo_pages.most_visited_translations_page
                 ._get_a_particular_translation_status(article_details['article_title'])),
                super().LOCALIZATION_DASHBOARD_NEEDS_TRANSLATION_STATUS
            )

        with allure.step("Navigating to the article translation page and verifying that no "
                         "banner is displayed"):
            self.sumo_pages.most_visited_translations_page._click_on_a_particular_article_status(
                article_details['article_title']
            )
            translation_url = self.get_page_url()
            expect(
                self.sumo_pages.translate_article_page._get_unready_for_translation_banner()
            ).to_be_hidden()

        with allure.step("Performing an article translation"):
            translation = self.sumo_pages.submit_kb_translation_flow._add_article_translation(
                approve_translation_revision=False
            )

        with check, allure.step("Navigating to the localization dashboard and verifying that the "
                                "correct status is displayed"):
            self.wait_for_given_timeout(2000)
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            check.equal(
                (self.sumo_pages.most_visited_translations_page
                 ._get_a_particular_translation_status(translation['translation_title'])),
                super().LOCALIZATION_DASHBOARD_NEEDS_REVIEW_STATUS
            )

        with check, allure.step("Navigating to the article translation and approving the "
                                "translation revision"):
            self.sumo_pages.most_visited_translations_page._click_on_a_particular_article_status(
                translation['translation_title']
            )
            self.sumo_pages.submit_kb_translation_flow.approve_kb_translation(
                translation['revision_id']
            )

        with check, allure.step("Navigating to the localization dashboard an verifying that the "
                                "correct status is displayed"):
            self.wait_for_given_timeout(2000)
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            check.equal(
                self.sumo_pages.most_visited_translations_page._get_updated_localization_status(
                    translation['translation_title']
                ),
                super().LOCALIZATION_DASHBOARD_TRANSLATED_STATUS
            )

        with allure.step("Deleting the parent article"):
            self.navigate_to_link(parent_article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

        with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                                "that the 404 page is returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    translation_url
                )
            response = navigation_info.value
            assert response.status == 404

    # C2490043
    @pytest.mark.kbArticleTranslation
    def test_revisions_cannot_be_marked_as_ready_for_l10n_if_lacking_permissions(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and marking it as ready for localization"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )
        article_url = self.get_page_url()

        with allure.step("Signing in with a different account that has no permissions to mark a "
                         "revision as ready for l10n"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
            ))

        with allure.step("Clicking on the ready for l10n button and verifying that it has no "
                         "effect"):
            self.sumo_pages.kb_article_show_history_page._click_on_ready_for_l10n_option(
                article_details['first_revision_id']
            )
            self.wait_for_given_timeout(2000)
            expect(
                self.sumo_pages.kb_article_show_history_page._get_l10n_modal_locator()
            ).to_be_hidden()

            expect(
                self.sumo_pages.kb_article_show_history_page._get_ready_for_localization_status(
                    article_details['first_revision_id']
                )
            ).to_be_hidden()

        with allure.step("Navigating to the localization dashboard and verifying that the "
                         "article is not listed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['l10n_most_visited_translations']
            )
            expect(
                (self.sumo_pages.most_visited_translations_page
                 ._get_a_particular_article_title_locator(article_details['article_title']))
            ).to_be_hidden()

        with allure.step("Navigating to the localization unreviewed page and verifying that the "
                         "article is not listed"):
            self.navigate_to_link(
                super().general_test_data['dashboard_links']['localization_unreviewed']
            )
            expect(
                self.sumo_pages.localization_unreviewed_page._get_listed_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Navigating back to the article and deleting it"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2316346, C2316347
    @pytest.mark.kbArticleTranslation
    def test_unsupported_locales_fallback(self):
        with allure.step("Verifying the unsupported locales fallback"):
            for key, value in NON_SUPPORTED_LOCALES.items():
                self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{key}/")
                if value is None:
                    expect(
                        self.page
                    ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)
                else:
                    expect(
                        self.page
                    ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{value}/")

    # C2625000
    @pytest.mark.kbArticleTranslation
    def test_fallback_languages(self):
        with allure.step("Verifying the language fallback"):
            for key, value in FALLBACK_LANGUAGES.items():
                self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{value}/")
                expect(
                    self.page
                ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{key}/")

    # C2316347
    @pytest.mark.kbArticleTranslation
    def test_supported_languages(self):
        with allure.step("Verifying that the users are redirected to the supported locales "
                         "successfully"):
            for locale in SUMO_LANGUAGES:
                if locale == 'xx':
                    continue
                else:
                    with self.page.expect_navigation() as navigation_info:
                        self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{locale}/")
                    response = navigation_info.value
                    assert response.status == 200
                    assert locale in self.get_page_url()

    # C2316350, C2316349
    @pytest.mark.kbArticleTranslation
    def test_sumo_locale_priority(self):
        with allure.step("Signing in with a non-admin account and changing the preferred profile "
                         "language"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
            ))

        with allure.step("Accessing the edit profile page and changing the language to ro"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            (self.sumo_pages.edit_my_profile_page
             ._select_preferred_language_dropdown_option_by_value("ro"))
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step("Navigating to the SUMO homepage without specifying the path in the "
                         "locale and verifying that the preferred locale is set"):
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/")

        with allure.step("Navigating to the SUMO homepage while using a lang query parameter and "
                         "verifying that the user is redirected to the specified locale inside "
                         "the param"):
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + "/?lang=de")
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/de/")

        with allure.step("Navigating back to the ro locale"):
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)

        with allure.step("Sending a request by modifying the 'Accept-Language' header to a "
                         "different locale"):
            headers = {
                'Accept-Language': 'it'
            }
            self.set_extra_http_headers(headers)
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/")

        with allure.step("Changing the preferred language back to english and signing out"):
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + '/en-US/')
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            (self.sumo_pages.edit_my_profile_page
             ._select_preferred_language_dropdown_option_by_value("en-US"))
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()
            self.delete_cookies()

        with allure.step("Sending the request with the modified 'Accept-Language' header set to "
                         "a different locale and verifying that the correct locale is displayed"):
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/it/")

        with allure.step("Sending the request with the modified 'Accept-Language' to point out "
                         "to an invalid locale and a fallback and verifying that the user is "
                         "redirected to the correct first fallback locale"):
            headers = {
                'Accept-Language': 'test, de, it'
            }
            self.set_extra_http_headers(headers)
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/de/")
