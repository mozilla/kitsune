import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from slugify import slugify
from kitsune.settings import FALLBACK_LANGUAGES, NON_SUPPORTED_LOCALES, SUMO_LANGUAGES
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages,
)
from playwright_tests.messages.explore_help_articles.kb_translation_messages import (
    KbTranslationMessages,
)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C2489548, C2490043, C946153
@pytest.mark.kbArticleTranslation
def test_not_ready_for_localization_articles_dashboard_status(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_translation_messages = KbTranslationMessages()
    test_user = create_user_factory(permissions=["review_revision", "mark_ready_for_l10n",
                                                 "delete_document"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article and approving it without marking it as "
                     "ready for localization"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True
        )

    with allure.step("Clicking on the Translate Article Editing Tools option and selecting "
                     "the ro locale"):
        sumo_pages.kb_article_page.click_on_translate_article_option()
        sumo_pages.translate_article_page.click_on_locale_from_list("ro")
        translation_ro_url = utilities.get_page_url()

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert (sumo_pages.translate_article_page.
                get_text_of_article_unready_for_translation_banner() == KBArticlePageMessages.
                KB_ARTICLE_NOT_READY_FOR_TRANSLATION_BANNER)

    with allure.step("Navigating to the localization dashboard and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.most_visited_translations_page.article_title(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['localization_unreviewed']
        )
        expect(sumo_pages.localization_unreviewed_page.listed_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating back to the translation page and performing a translation"):
        utilities.navigate_to_link(translation_ro_url)
        translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=False
        )

    with allure.step("Navigating to the localization dashboard and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.most_visited_translations_page.article_title(
            translation['translation_title'])).to_be_hidden()

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['localization_unreviewed']
        )
        expect(sumo_pages.localization_unreviewed_page.listed_article(
            translation['translation_title'])).to_be_visible()

    with allure.step("Verifying that the correct modified by text is displayed"):
        assert (sumo_pages.localization_unreviewed_page.get_modified_by_text(
            translation['translation_title']) == kb_translation_messages.
            get_unreviewed_localization_modified_by_text(test_user["username"]))

    with allure.step("Clicking on the article approving the revision"):
        sumo_pages.localization_unreviewed_page.click_on_a_listed_article(
            translation['translation_title']
        )
        sumo_pages.submit_kb_translation_flow.approve_kb_translation(translation['revision_id'])

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is not displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.localization_unreviewed_page.listed_article(
            translation['translation_title'])).to_be_hidden()

    with allure.step("Navigating to the localization dashboard and verifying that the article is"
                     " not displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.localization_unreviewed_page.listed_article(
            translation['translation_title'])).to_be_hidden()

    with allure.step("Navigating to the parent article and marking it as ready for l10n"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_show_history_page.click_on_ready_for_l10n_option(
            article_details['first_revision_id']
        )
        sumo_pages.kb_article_show_history_page.click_on_submit_l10n_readiness_button(
            revision_id=article_details['first_revision_id'])

    with allure.step("Navigating to the localization dashboard and verifying that the article is"
                     " displayed with the correct status"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        assert (sumo_pages.most_visited_translations_page.
                get_updated_localization_status(translation['translation_title']
                                                ) == kb_translation_messages.
                LOCALIZATION_DASHBOARD_TRANSLATED_STATUS)

    with allure.step("Deleting the parent article"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with allure.step("Manually navigating to the 'Discuss' endpoint and verifying that the 404"
                     " page is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(translation["translation_url"])
        response = navigation_info.value
        assert response.status == 404


# C2489548
@pytest.mark.smokeTest
@pytest.mark.kbArticleTranslation
def test_ready_for_localization_articles_dashboard_status(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_translation_messages = KbTranslationMessages()
    test_user = create_user_factory(permissions=["review_revision", "mark_ready_for_l10n",
                                                 "delete_document"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article and marking it as ready for localization"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, ready_for_localization=True
        )

    with allure.step("Navigating to the localization dashboard and verifying that the correct"
                     " status is displayed"):
        expect(sumo_pages.kb_article_show_history_page.revision_status(
            article_details["first_revision_id"])).to_be_visible()
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        assert (sumo_pages.most_visited_translations_page.
                get_a_particular_translation_status(article_details['article_title']
                                                    ) == kb_translation_messages.
                LOCALIZATION_DASHBOARD_NEEDS_TRANSLATION_STATUS)

    with check, allure.step("Navigating to the article translation page and verifying that no "
                            "banner is displayed"):
        sumo_pages.most_visited_translations_page.click_on_a_particular_article_status(
            article_details['article_title'])
        expect(sumo_pages.translate_article_page.translating_an_unready_article_banner
               ).to_be_hidden()

    with allure.step("Performing an article translation"):
        translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=False
        )

    with allure.step("Navigating to the localization dashboard and verifying that the correct"
                     " status is displayed"):
        sumo_pages.kb_article_show_history_page.is_revision_current(translation['revision_id'])
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        assert (sumo_pages.most_visited_translations_page.
                get_a_particular_translation_status(translation['translation_title']
                                                    ) == kb_translation_messages.
                LOCALIZATION_DASHBOARD_NEEDS_REVIEW_STATUS
                )

    with allure.step("Navigating to the article translation and approving the translation"
                     " revision"):
        sumo_pages.most_visited_translations_page.click_on_a_particular_article_status(
            translation['translation_title']
        )
        sumo_pages.submit_kb_translation_flow.approve_kb_translation(translation['revision_id'])

    with allure.step("Navigating to the localization dashboard an verifying that the correct"
                     " status is displayed"):
        sumo_pages.kb_article_show_history_page.is_revision_current(translation['revision_id'])
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        assert (sumo_pages.most_visited_translations_page.
                get_updated_localization_status(translation['translation_title']
                                                ) == kb_translation_messages.
                LOCALIZATION_DASHBOARD_TRANSLATED_STATUS)

    with allure.step("Deleting the parent article"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with allure.step("Manually navigating to the 'Discuss' endpoint and verifying that the 404"
                     " page is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(translation["translation_url"])
        response = navigation_info.value
        assert response.status == 404


# C2490043
@pytest.mark.smokeTest
@pytest.mark.kbArticleTranslation
def test_revisions_cannot_be_marked_as_ready_for_l10n_if_lacking_permissions(page: Page,
                                                                             create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["review_revision", "mark_ready_for_l10n"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article and marking it as ready for localization"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True
        )

    with allure.step("Signing in with a different account that has no permissions to mark a "
                     "revision as ready for l10n"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Clicking on the ready for l10n button and verifying that it has no "
                     "effect"):
        sumo_pages.kb_article_show_history_page.click_on_ready_for_l10n_option(
            article_details['first_revision_id']
        )
        utilities.wait_for_given_timeout(2000)
        expect(sumo_pages.kb_article_show_history_page.l10n_modal).to_be_hidden()

        expect(
            sumo_pages.kb_article_show_history_page.ready_for_localization_status(
                article_details['first_revision_id']
            )
        ).to_be_hidden()

    with allure.step("Navigating to the localization dashboard and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.most_visited_translations_page.article_title(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['localization_unreviewed']
        )
        expect(sumo_pages.localization_unreviewed_page.listed_article(
            article_details['article_title'])).to_be_hidden()


# C2316346, C2316347
@pytest.mark.kbArticleTranslation
def test_unsupported_locales_fallback(page: Page):
    utilities = Utilities(page)
    with allure.step("Verifying the unsupported locales fallback"):
        for key, value in NON_SUPPORTED_LOCALES.items():
            utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{key}/")
            if value is None:
                expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)
            else:
                expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{value}/")


# C2625000
@pytest.mark.kbArticleTranslation
def test_fallback_languages(page: Page):
    utilities = Utilities(page)
    with allure.step("Verifying the language fallback"):
        for key, value in FALLBACK_LANGUAGES.items():
            utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{value}/")
            expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{key}/")


# C2316347
@pytest.mark.kbArticleTranslation
def test_supported_languages(page: Page):
    utilities = Utilities(page)
    with allure.step("Verifying that the users are redirected to the supported locales "
                     "successfully"):
        for locale in SUMO_LANGUAGES:
            if locale == 'xx':
                continue
            else:
                with page.expect_navigation() as navigation_info:
                    utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{locale}/")
                response = navigation_info.value
                assert response.status == 200
                assert locale in utilities.get_page_url()


# C2316350, C2316349
@pytest.mark.kbArticleTranslation
def test_sumo_locale_priority(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account and changing the "
                     f"preferred profile language"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the edit profile page and changing the language to ro"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.select_preferred_language_dropdown_option_by_value("ro")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()

    with allure.step("Navigating to the SUMO homepage without specifying the path in the "
                     "locale and verifying that the preferred locale is set"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/")

    with allure.step("Navigating to the SUMO homepage while using a lang query parameter and "
                     "verifying that the user is redirected to the specified locale inside "
                     "the param"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + "/?lang=de")
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/de/")

    with allure.step("Navigating back to the ro locale"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)

    with allure.step("Sending a request by modifying the 'Accept-Language' header to a "
                     "different locale"):
        headers = {'Accept-Language': 'it'}
        utilities.set_extra_http_headers(headers)
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/")

    with allure.step("Changing the preferred language back to english and signing out"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + '/en-US/')
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.select_preferred_language_dropdown_option_by_value("en-US")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()
        utilities.delete_cookies()

    with allure.step("Sending the request with the modified 'Accept-Language' header set to "
                     "a different locale and verifying that the correct locale is displayed"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/it/")

    with allure.step("Sending the request with the modified 'Accept-Language' to point out "
                     "to an invalid locale and a fallback and verifying that the user is "
                     "redirected to the correct first fallback locale"):
        headers = {'Accept-Language': 'test, de, it'}
        utilities.set_extra_http_headers(headers)
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/de/")


# C3016012
@pytest.mark.kbArticleTranslation
def test_topic_inheritance_from_parent(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    original_topic_listing_page = "https://support.allizom.org/ro/products/firefox/accounts"
    new_topic_listing_page = ("https://support.allizom.org/ro/products/firefox/settings/"
                              "customization")
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"],
                                    permissions=["delete_document"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article and approving it without marking it as "
                     "ready for localization"):
        parent_article_info = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Creating a new translation in the ro locale"):
        translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=True, locale="ro")

    with allure.step("Navigating to the topic listing page and verifying that the translation is"
                     " successfully displayed"):
        utilities.navigate_to_link(original_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_visible()

    with allure.step("Navigating to the parent article and editing it's metadata by adding a new "
                     "topic"):
        utilities.navigate_to_link(parent_article_info["article_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            topics=["Settings", "Customization"]
        )

    with allure.step("Navigating to the first topic listing page and verifying that the "
                     "translations is successfully displayed"):
        utilities.navigate_to_link(original_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_visible()

    with allure.step("Navigating to the new topic listing page and verifying that the translations"
                     " is successfully displayed"):
        utilities.navigate_to_link(new_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_visible()

    with allure.step("Removing the old topic from the parent article"):
        utilities.navigate_to_link(parent_article_info["article_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(topics="Accounts")

    with allure.step("Navigating to the first topic listing page and verifying that the"
                     " translation is not displayed"):
        utilities.navigate_to_link(original_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_hidden()

    with allure.step("Navigating to the new topic listing page and verifying that the translation"
                     " is displayed"):
        utilities.navigate_to_link(new_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_visible()

    with allure.step("Deleting the parent article"):
        utilities.navigate_to_link(parent_article_info["article_url"])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with allure.step("Verifying that the translation is not visible in both the original and new "
                     "topic listing pages"):
        utilities.navigate_to_link(original_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_hidden()

        utilities.navigate_to_link(new_topic_listing_page)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            translation['translation_title'])).to_be_hidden()


# C3059082
@pytest.mark.kbArticleTranslation
def test_article_translation_on_locale_switch(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)
        sumo_pages.kb_article_page.click_on_article_option()
        article_url = utilities.get_page_url()

    with allure.step("Creating a new translation in the ro locale"):
        ro_translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=True, locale="ro",
            title=f"Articol de test {article_details['article_title']}",
            slug=f"articol-de-test-{slugify(article_details['article_title'])}")

    with allure.step("Navigating back to the english article"):
        utilities.navigate_to_link(article_details['article_url'])

    with allure.step("Creating a new translation in the de locale"):
        de_translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=True, locale="de",
            title=f"Testartikel {article_details['article_title']}",
            slug=f"testartikel-{slugify(article_details['article_title'])}")

    with allure.step("Navigating back to the english article and signing out from SUMO"):
        utilities.navigate_to_link(article_url)
        utilities.delete_cookies()

    with allure.step("Switching the page locale to 'ro' and verifying that the translated version"
                     " is successfully displayed"):
        sumo_pages.footer_section.switch_to_a_locale("ro")
        expect(page).to_have_url(
            HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/kb/" + ro_translation['translation_slug'])
        assert (sumo_pages.kb_article_page.
                get_text_of_article_title() == ro_translation['translation_title'])

    with allure.step("Switch the page locale to 'de' and verifying that the translated version is"
                     " successfully displayed"):
        sumo_pages.footer_section.switch_to_a_locale("de")
        expect(page).to_have_url(
            HomepageMessages.STAGE_HOMEPAGE_URL + "/de/kb/" + de_translation['translation_slug'])
        assert (sumo_pages.kb_article_page.
                get_text_of_article_title() == de_translation['translation_title'])

    with allure.step("Switching to the 'fr' locale and verifying that 404 is returned"):
        with page.expect_response("**/kb/**") as response_info:
            sumo_pages.footer_section.switch_to_a_locale("fr")
        response = response_info.value
        assert response.status == 404

    with allure.step("Switching back to the 'en-US' locale and verifying that the article is"
                     " displayed in the english form"):
        sumo_pages.footer_section.switch_to_a_locale("en-US")
        expect(page).to_have_url(
            HomepageMessages.STAGE_HOMEPAGE_URL + "/en-US/kb/" + article_details['article_slug'])
        assert (sumo_pages.kb_article_page.
                get_text_of_article_title() == article_details['article_title'])

    with allure.step("Switching to the 'fr' locale and verifying that the article is displayed in"
                     " the english form"):
        sumo_pages.footer_section.switch_to_a_locale("fr")
        expect(page).to_have_url(
            HomepageMessages.STAGE_HOMEPAGE_URL + "/fr/kb/" + article_details['article_slug'])
        assert (sumo_pages.kb_article_page.
                get_text_of_article_title() == article_details['article_title'])


@pytest.mark.kbArticleTranslation
def test_locale_redirect_from_article_without_en_us_parent(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])
    with allure.step(f"Signing in with an {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article directly inside the RO locale"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, locale="ro", article_category="ro-translation-category"
        )
        sumo_pages.kb_article_page.click_on_a_particular_breadcrumb(
            article_details['article_title']
        )
        article_url = utilities.get_page_url()

    with allure.step("Switching the page locale to en-US and verifying that 404 is returned"):
        with page.expect_response("**/kb/**") as response_info:
            sumo_pages.footer_section.switch_to_a_locale("en-US")
        response = response_info.value
        assert response.status == 404

    with allure.step("Navigating back to the article"):
        utilities.navigate_to_link(article_url)

    with allure.step("Switching the locale to de and verifying that 404 is returned"):
        with page.expect_response("**/kb/**") as response_info:
            sumo_pages.footer_section.switch_to_a_locale("de")
        response = response_info.value
        assert response.status == 404
