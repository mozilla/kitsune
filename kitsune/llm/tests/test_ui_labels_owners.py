import json
import re
from unittest.mock import patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from kitsune.llm.l10n.ui_labels.owners import lookup
from kitsune.llm.l10n.ui_labels.owners.lookup import get_owners
from kitsune.llm.models import UILabelOwners, UISpotList, UIStringCatalog, UIStringSource
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase, login_to_admin
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

ARTICLE = (
    "= Windows =\n"
    "Open {menu Settings}<!-- {menu Hidden} -->.\n"
    "= Firefox =\n"
    "Click {menu View}, set {pref debug}, then {button OK}.\n"
)


def strings(*spots):
    return [{"id": string_id, "text": "View", "spot": spot} for spot, string_id in spots]


class GetOwnersTests(TestCase):
    def setUp(self):
        self.document = DocumentFactory(products=[ProductFactory(slug="firefox")])
        self.spot_list = UISpotList.objects.create(
            owner="firefox",
            strings_by_text={"view": strings((0, "menu:view"), (1, "a:view"), (1, "b:view"))},
        )
        UISpotList.objects.create(
            owner="thunderbird", strings_by_text={"view": strings((0, "x"), (1, "y"))}
        )
        UIStringCatalog.objects.create(
            owner="firefox",
            source=UIStringSource.objects.create(name="firefox-l10n"),
            locale="en-US",
            comments={"menu:view": "The View\n  menu"},
        )
        self.replies = [
            {"label": 0, "owner": "unknown", "unknown_reason": "os"},
            {"label": 1, "owner": "firefox", "spot": "s2"},
            {"label": 2, "owner": "config"},
            {"label": 3, "owner": "firefox"},
        ]
        self.sent = []
        self.enterContext(patch.object(lookup, "get_llm", return_value=RunnableLambda(self.llm)))
        self.enterContext(patch.object(lookup, "redis_client"))

    def llm(self, prompt):
        self.sent.append([message.content for message in prompt.to_messages()])
        return AIMessage(content=json.dumps({"answers": self.replies}))

    def revision(self):
        return ApprovedRevisionFactory(document=self.document, content=ARTICLE)

    def owners(self, revision):
        return {
            position: (
                label_owner.text,
                label_owner.owner,
                label_owner.unknown_reason,
                label_owner.spot,
            )
            for position, label_owner in get_owners(revision).items()
        }

    def asked(self):
        """Return the numbers of the labels the LLM was last asked about."""
        labels = self.sent[-1][1].split("\nArticle:\n")[0]
        return [int(number) for number in re.findall(r"\n⟦(\d+)⟧", labels)]

    def test_the_llm_reads_the_whole_article_with_a_number_before_each_label(self):
        with patch.object(lookup, "MAX_EXAMPLES", 1):
            get_owners(self.revision())
        system, article = self.sent[0]

        self.assertIn("- firefox-android: Firefox for Android", system)
        self.assertIn(f"Title: {self.document.title}\nProducts: firefox\n", article)
        # Spots are shown for the owners tied to the article's products, not for Thunderbird.
        self.assertIn(
            "⟦0⟧{menu Settings}\n"
            "  owners with this text: none\n"
            "\n"
            "⟦1⟧{menu View}\n"
            "  owners with this text: firefox, thunderbird\n"
            "  spots if the owner is firefox:\n"
            "    s1: menu:view (The View menu)\n"
            "    s2: a:view … and 1 more\n",
            article,
        )
        self.assertTrue(
            article.endswith(
                "Article:\n"
                "= Windows =\n"
                "Open ⟦0⟧{menu Settings}.\n"
                "= Firefox =\n"
                "Click ⟦1⟧{menu View}, set ⟦2⟧{pref debug}, then ⟦3⟧{button OK}.\n"
            )
        )

    def test_an_answer_keeps_only_what_was_asked(self):
        for replies, expected in (
            (
                [
                    {"label": 0, "owner": "windows", "unknown_reason": "os"},
                    {"label": 1, "owner": "firefox", "spot": "s2"},
                    {"label": 2, "owner": "config"},
                    {"label": 9, "owner": "firefox"},
                ],
                {
                    0: ("Settings", "unknown", "os", None),
                    1: ("View", "firefox", "", ["a:view", "b:view"]),
                    2: ("debug", "config", "", None),
                },
            ),
            (
                [
                    {"label": 0, "owner": "unknown", "unknown_reason": "magic"},
                    {"label": 1, "owner": "firefox", "spot": "none"},
                    {"label": 3, "owner": "config"},
                ],
                {
                    0: ("Settings", "unknown", "unclear", None),
                    1: ("View", "firefox", "", []),
                    3: ("OK", "unknown", "unclear", None),
                },
            ),
            # A spot that wasn't shown, or no spot at all, counts as none.
            (
                [{"label": 1, "owner": "firefox", "spot": "s7"}],
                {1: ("View", "firefox", "", [])},
            ),
            (
                [{"label": 1, "owner": "thunderbird"}],
                {1: ("View", "thunderbird", "", None)},
            ),
        ):
            with self.subTest(replies):
                self.replies = replies
                self.assertEqual(self.owners(self.revision()), expected)

    def test_owners_are_asked_once_and_saved(self):
        self.replies, skipped = self.replies[:3], self.replies[3:]
        revision = self.revision()
        expected = {
            0: ("Settings", "unknown", "os", None),
            1: ("View", "firefox", "", ["a:view", "b:view"]),
            2: ("debug", "config", "", None),
        }

        self.assertEqual(self.owners(revision), expected)
        self.assertEqual(self.asked(), [0, 1, 2, 3])

        # The label the LLM skipped is asked about again, and nothing else.
        self.replies = skipped
        self.assertEqual(self.owners(revision), expected | {3: ("OK", "firefox", "", None)})
        self.assertEqual(self.asked(), [3])

        self.owners(revision)
        self.assertEqual(len(self.sent), 2)

    def test_a_label_is_asked_again_when_its_saved_owner_no_longer_holds(self):
        revision = self.revision()
        get_owners(revision)
        self.replies = []

        for asked, change in (
            # A sync split the spot that View was given.
            (
                [1],
                {
                    "strings_by_text": {
                        "view": strings((0, "menu:view"), (1, "a:view"), (2, "b:view"))
                    }
                },
            ),
            # A sync gave OK, which had one spot and so no choice to make, a second one.
            (
                [3],
                {
                    "strings_by_text": {
                        "view": strings((0, "a:view"), (0, "b:view")),
                        "ok": strings((0, "c"), (1, "d")),
                    }
                },
            ),
        ):
            with self.subTest(asked):
                self.spot_list.update(**change)
                get_owners(revision)
                self.assertEqual(self.asked(), asked)

        # A new answer replaces the one that no longer held.
        self.replies = [{"label": 3, "owner": "firefox", "spot": "s1"}]
        self.assertEqual(self.owners(revision)[3], ("OK", "firefox", "", ["c"]))

        # A saved owner that isn't about the label at its position doesn't count.
        record = UILabelOwners.objects.get(revision=revision)
        record.owners["0"]["text"] = "Options"
        record.save()
        get_owners(revision)
        self.assertEqual(self.asked(), [0])

        # A newer version of the question makes every saved owner count as missing.
        with patch.object(lookup, "ANSWER_VERSION", "2:model"):
            get_owners(revision)
            self.assertEqual(self.asked(), [0, 1, 2, 3])

    def test_an_answer_of_none_is_kept(self):
        self.replies[1] = {"label": 1, "owner": "firefox", "spot": "none"}
        revision = self.revision()

        self.assertEqual(self.owners(revision)[1], ("View", "firefox", "", []))
        self.owners(revision)
        self.assertEqual(len(self.sent), 1)

    def test_a_task_that_waited_in_vain_takes_what_is_saved(self):
        revision = self.revision()
        UILabelOwners.objects.create(
            revision=revision,
            owners={
                0: {"kind": "menu", "text": "Settings", "owner": "unknown", "unknown_reason": "os"}
            },
            answer_version=lookup.ANSWER_VERSION,
        )

        with patch.object(lookup, "redis_client") as redis_client:
            redis_client.return_value.lock.return_value.acquire.return_value = False
            self.assertEqual(self.owners(revision), {0: ("Settings", "unknown", "os", None)})

        self.assertEqual(self.sent, [])

    def test_the_admin_shows_what_was_chosen_for_a_revision(self):
        revision = self.revision()
        get_owners(revision)
        login_to_admin(self.client, UserFactory(is_staff=True, is_superuser=True))

        url = reverse("admin:llm_uilabelowners_changelist")
        self.assertContains(self.client.get(url, {"q": revision.id}), self.document.title)
        self.assertNotContains(self.client.get(url, {"q": "another"}), self.document.title)

        shown = self.client.get(reverse("admin:llm_uilabelowners_change", args=[revision.id]))
        self.assertContains(
            shown,
            "0  {menu Settings} → unknown: os\n"
            "1  {menu View} → firefox, spot: a:view, b:view\n"
            "2  {pref debug} → config\n"
            "3  {button OK} → firefox</pre>",
        )
