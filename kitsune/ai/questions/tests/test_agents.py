from unittest import skipUnless
import os

from django.contrib.contenttypes.models import ContentType
from django.test import TransactionTestCase

from kitsune.ai.questions.agents import classify
from kitsune.flagit.models import FlaggedObject
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.questions.tests import QuestionFactory
from kitsune.users.models import Profile


@skipUnless(
    os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    "Google application credentials have not been configured.",
)
class ClassifyQuestionsTests(TransactionTestCase):

    def setUp(self):
        self.sumo_bot = Profile.get_sumo_bot()

        self.firefox = firefox = ProductFactory(title="Firefox", slug="firefox")
        self.focus = focus = ProductFactory(title="Firefox Focus", slug="focus-firefox")
        self.mobile = mobile = ProductFactory(title="Firefox for Android", slug="mobile")
        self.ios = ios = ProductFactory(title="Firefox for iOS", slug="ios")
        self.ffe = ffe = ProductFactory(title="Firefox for Enterprise", slug="firefox-enterprise")
        self.relay = relay = ProductFactory(title="Firefox Relay", slug="relay")
        self.mdn = mdn = ProductFactory(title="MDN Plus", slug="mdn-plus")
        self.monitor = monitor = ProductFactory(title="Mozilla Monitor", slug="monitor")
        self.vpn = vpn = ProductFactory(title="Mozilla VPN", slug="firefox-private-network-vpn")
        self.tb = tb = ProductFactory(title="Thunderbird", slug="thunderbird")
        self.tba = tba = ProductFactory(
            title="Thunderbird for Android", slug="thunderbird-android"
        )
        self.pocket = pocket = ProductFactory(title="Pocket", slug="pocket")
        self.ma = ma = ProductFactory(
            title="Mozilla Account", slug="mozilla-account", visible=False
        )

        t1 = TopicFactory(
            title="Accessibility",
            description=(
                "Learn about Mozilla products' accessibility features and settings for better"
                " usability."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to accessibility features and settings."
                    " This might include screen reader compatibility, ability to navigate sites"
                    " via keyboard shortcuts, voice-to-text compatibility, color combinations with"
                    " a contrast ratio intended for increased legibility, etc."
                ),
            ),
            products=[firefox, mobile, ios, ma, pocket, tb, tba],
        )
        TopicFactory(
            title="Reader View",
            description="Comfortably read web pages without distractions.",
            parent=t1,
            metadata=dict(
                description="Content, questions, or issues related to our Reader Mode feature.",
            ),
            products=[firefox, mobile, ios],
        )
        t1_2 = TopicFactory(
            title="Text-to-speech",
            description="Read web pages aloud.",
            parent=t1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Text-to-speech accessibility tools."
                ),
            ),
            products=[firefox, mobile, ios, pocket],
        )
        TopicFactory(
            title="Listen",
            description="Listen to your favorite podcasts and audiobooks.",
            parent=t1_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the Listen functionality of"
                    " Text-to-speech accessibility tools."
                ),
            ),
            products=[firefox, mobile, ios, pocket],
        )
        t2 = TopicFactory(
            title="Accounts",
            description="Manage your accounts and profiles for Mozilla’s products and services.",
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing accounts and profiles (e.g."
                    " - including Mozilla Accounts and Firefox profiles)."
                ),
            ),
            products=[firefox, mobile, ffe, ios, mdn, ma, vpn, pocket, tb, tba],
        )
        t2_1 = TopicFactory(
            title="Account management",
            description="Manage your account settings and preferences.",
            parent=t2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing account settings and"
                    " preferences."
                ),
            ),
            products=[firefox, mobile, ios, ma, vpn, pocket, tb, tba],
        )
        TopicFactory(
            title="Edit account details",
            description="Edit your account details.",
            parent=t2_1,
            metadata=dict(
                description="Content, questions, or issues related to updating account details.",
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Location",
            description="Change your location.",
            parent=t2_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Account location or location"
                    " services."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Account recovery",
            description="Recover your account if you lose access to it or encounter issues.",
            parent=t2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to recovering a user's account."
                ),
            ),
            products=[mdn, ma, vpn, pocket],
        )
        TopicFactory(
            title="Profiles",
            description="Create and manage user profiles.",
            parent=t2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to creating and managing settings for"
                    " user profiles."
                ),
            ),
            products=[firefox, mobile, ffe, ios, ma, pocket, tb, tba],
        )
        t3 = TopicFactory(
            title="Backup, recovery, and sync",
            description=(
                "Sync your data across different platforms and devices, backup what’s important,"
                " and recover it if it’s lost."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to syncing data across different"
                    " platforms and devices, backing up personal data, and recovery methods if a"
                    " user loses data."
                ),
            ),
            products=[firefox, mobile, ios, ma],
        )
        TopicFactory(
            title="Backup data",
            description=(
                "From passwords to bookmarks, discover ways to back up your important data."
            ),
            parent=t3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to how users can back up data, like"
                    " passwords and bookmarks, with backup tools and functionality."
                ),
            ),
            products=[firefox, mobile, ios, ma],
        )
        t3_2 = TopicFactory(
            title="Recover data",
            description="Learn how to recover your lost data.",
            parent=t3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to recovering lost data like bookmarks,"
                    " saved tabs, settings, or account data."
                ),
            ),
            products=[firefox, mobile, ios, ma],
        )
        TopicFactory(
            title="Sync and backup confusion",
            description="Troubleshoot sync and backup confusion.",
            parent=t3_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to users who expect the Firefox Sync"
                    " tool to work as a backup. This could apply to users who are generally"
                    " confused about the difference between syncing and backing up data, but we"
                    " mostly see this in the context of Firefox Sync."
                ),
            ),
            products=[firefox, mobile, ios, ma],
        )
        self.sync_data = TopicFactory(
            title="Sync data",
            description="Sync your data across different platforms and devices.",
            parent=t3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to syncing data across platforms,"
                    " devices, browsers, etc. This topic can apply to data like passwords, browser"
                    " sessions, tabs, bookmarks, etc."
                ),
            ),
            products=[firefox, mobile, ios, ma],
        )
        TopicFactory(
            title="Sync configuration",
            description="Change your sync configuration.",
            parent=self.sync_data,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing data sync settings or"
                    " configuring Firefox Sync across devices."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Sync failure",
            description="Troubleshoot sync issues.",
            parent=self.sync_data,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to data sync not functioning properly"
                    " across devices (either with Firefox Sync or another product's sync"
                    " functionality)."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t4 = TopicFactory(
            title="Billing and subscriptions",
            description=(
                "Manage your subscriptions and payment details for Mozilla’s premium products."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to signing up, settings, and managing"
                    " billing for Mozilla product subscriptions."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        t4_1 = TopicFactory(
            title="Manage billing",
            description="Manage your payment details and billing information.",
            parent=t4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing billing for product"
                    " subscriptions (i.e. - adding or removing payment cards, changing billing"
                    " addresses, etc.)."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        TopicFactory(
            title="Billing inquiry",
            description="Inquire about your billing.",
            parent=t4_1,
            metadata=dict(
                description=(
                    "General questions or issues related to billing for product subscriptions such"
                    " as billing cadences, taxes, or payment methods."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        TopicFactory(
            title="Declined payment",
            description="Troubleshoot declined payment issues.",
            parent=t4_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to payments or forms of payment that"
                    " are declined."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        TopicFactory(
            title="Sales tax",
            description="Troubleshoot sales tax issues.",
            parent=t4_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to how sales tax is applied to"
                    " Mozilla's product subscriptions."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        t4_2 = TopicFactory(
            title="Manage subscriptions",
            description="Manage your subscriptions to Mozilla’s premium products and services.",
            parent=t4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing subscriptions to one or"
                    " more of Mozilla's premium products, such as subscription bundling, how to"
                    " cancel or change subscription tiers, and more."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        TopicFactory(
            title="Cancellation",
            description="Troubleshoot cancellation issues.",
            parent=t4_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to cancelling a subscription to one or"
                    " more of Mozilla's premium products."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        TopicFactory(
            title="Upgrade/downgrade subscription",
            description="Troubleshoot upgrade/downgrade subscription issues.",
            parent=t4_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to upgrading or downgrading a"
                    " subscription to a different tier of service."
                ),
            ),
            products=[relay, mdn, ma, monitor, vpn, pocket],
        )
        self.browse = TopicFactory(
            title="Browse",
            description=(
                "Explore how to navigate the web efficiently and effectively with Mozilla’s"
                " products."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to browsing the web with Firefox."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, pocket],
        )
        t5_1 = TopicFactory(
            title="Article View",
            description="Comfortably read web pages without distractions.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Pocket's Article View feature."
                ),
            ),
            products=[pocket],
        )
        TopicFactory(
            title="Customized reader",
            description="Troubleshoot customized reader issues.",
            parent=t5_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to customizing Pocket's reader feature."
                ),
            ),
            products=[pocket],
        )
        t5_2 = TopicFactory(
            title="Audio and Video",
            description="Everything you need to know about audio and video.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to audio/video features and"
                    " functionality (i.e. -  PiP, video players, music streaming, etc.) in Mozilla"
                    " products, including related settings."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="PiP",
            description="Troubleshoot picture in picture issues.",
            parent=t5_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the Picture-in-Picture feature"
                    " within Firefox, including related settings."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Bookmarks",
            description="Save and organize your favorite web content with bookmarks.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing saved bookmarks and/or the"
                    " bookmarks toolbar in Firefox."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t5_4 = TopicFactory(
            title="History",
            description="View and manage your browsing history.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing, navigating, or removing"
                    " browsing history."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Cookies",
            description="Cookies as they relate to browser history",
            parent=t5_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues about cookies/cache as they relate to the"
                    " browser history."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t5_5 = TopicFactory(
            title="Home screen",
            description="Add Mozilla's products to your home screen for easy access.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to navigating and customizing the"
                    " default screen of an app (i.e. - Homepage or New Tab in Firefox), including"
                    " related settings"
                ),
            ),
            products=[firefox, focus, mobile, ios, pocket],
        )
        TopicFactory(
            title="Dashboard",
            description="Troubleshoot dashboard issues.",
            parent=t5_5,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to dashboards as they appear in"
                    " Mozilla's products. For example, the dashboard on the homepage of Firefox"
                    " that displays a user's shortcuts, recently visited tabs, bookmarks and"
                    " collections."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="New tab",
            description="Troubleshoot new tab issues.",
            parent=t5_5,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Firefox New Tab, including how it"
                    " behaves, what is displayed in a new tab, or users wanting to stop the app"
                    " from open everything in a new tab."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t5_6 = TopicFactory(
            title="Images and documents",
            description="Everything you need to know about images and documents.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to saving, managing, interacting with"
                    " document or images with Mozilla's products."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Images",
            description="Troubleshoot images issues.",
            parent=t5_6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to image files (i.e. - how to download"
                    " and save images, how they are displayed in app, etc.)"
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="PDFs",
            description="Troubleshoot PDFs issues.",
            parent=t5_6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to PDF files (i.e. - how to download"
                    " and save PDFs, how to open PDF files, and any PDF-related functionality)."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t5_7 = TopicFactory(
            title="Links",
            description="Use web links in Mozilla's products.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to using web links/URL functionality"
                    " and navigation."
                ),
            ),
            products=[firefox, focus, mobile, ios, pocket],
        )
        TopicFactory(
            title="Recommendations",
            description="Troubleshoot recommendations issues.",
            parent=t5_7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Pocket's article recommendations."
                ),
            ),
            products=[pocket],
        )
        self.tabs = TopicFactory(
            title="Tabs",
            description="Organize and manage your tabs for better browsing.",
            parent=self.browse,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to organizing and managing browser tabs"
                    " for better navigation and browsing, including related settings."
                ),
            ),
            products=[firefox, focus, mobile, ios],
        )
        t6 = TopicFactory(
            title="Download and save",
            description="Manage your downloaded files and saved content",
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing downloaded files and saving"
                    " content, including related settings."
                ),
            ),
            products=[firefox, mobile, ios, mdn, pocket],
        )
        t6_1 = TopicFactory(
            title="Downloads",
            description="Manage and troubleshoot your downloads.",
            parent=t6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing how downloaded files are"
                    " handled and where they’re saved, including related settings."
                ),
            ),
            products=[firefox, mobile, ios, mdn],
        )
        TopicFactory(
            title="Download failure",
            description="Troubleshoot download failure issues.",
            parent=t6_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to files failing to download a file in"
                    " an app or product."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Print",
            description="Troubleshoot print issues.",
            parent=t6_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to printing (i.e. - the in-browser"
                    " Print function, printing images, documents, or emails, etc.)"
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t6_2 = TopicFactory(
            title="Save content",
            description="Save your favorite content for later.",
            parent=t6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to saving content like articles,"
                    " images, etc."
                ),
            ),
            products=[firefox, mobile, ios, mdn, pocket],
        )
        TopicFactory(
            title="Highlighting",
            description="Troubleshoot highlighting issues.",
            parent=t6_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the highlight function in Pocket."
                ),
            ),
            products=[pocket],
        )
        TopicFactory(
            title="Missing items",
            description="Troubleshoot missing items issues.",
            parent=t6_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to saved articles going missing in"
                    " Pocket."
                ),
            ),
            products=[pocket],
        )
        TopicFactory(
            title="Permanent library",
            description="Troubleshoot permanent library issues.",
            parent=t6_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the Permanent Library premium"
                    " feature in Pocket."
                ),
            ),
            products=[pocket],
        )
        TopicFactory(
            title="Reading list",
            description="Troubleshoot reading list issues.",
            parent=t6_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to saving webpages or articles to read"
                    " later using Firefox or Pocket's Reading List feature."
                ),
            ),
            products=[firefox, mobile, ios, pocket],
        )
        t7 = TopicFactory(
            title="Email and messaging",
            description="Read, send, and manage your emails and messages.",
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to emails, email providers and"
                    " services, and instant messaging."
                ),
            ),
            products=[relay, tb, tba],
        )
        TopicFactory(
            title="Attachments",
            description="Learn how to use and manage email attachments.",
            parent=t7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to file attachments to sent or received"
                    " emails."
                ),
            ),
            products=[tb, tba],
        )
        t7_2 = TopicFactory(
            title="Calendar",
            description="Manage your calendar events and schedules.",
            parent=t7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the built in calendar functionality"
                    " in Thunderbird."
                ),
            ),
            products=[tb, tba],
        )
        TopicFactory(
            title="Events",
            description="Troubleshoot events issues.",
            parent=t7_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to creating and saving events in the"
                    " Calendar in Thunderbird."
                ),
            ),
            products=[tb, tba],
        )
        TopicFactory(
            title="Contacts",
            description="Manage your email contacts.",
            parent=t7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to saving and managing contacts in"
                    " email and messaging."
                ),
            ),
            products=[tb, tba],
        )
        TopicFactory(
            title="Import and export email",
            description="Import and export your emails for backup or transfer.",
            parent=t7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to importing and exporting email"
                    " messages between devices or platforms."
                ),
            ),
            products=[tb, tba],
        )
        TopicFactory(
            title="Instant messaging",
            description="Features and functionality to use with instant messaging.",
            parent=t7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to instant messaging features or"
                    " services."
                ),
            ),
            products=[relay, tb, tba],
        )
        TopicFactory(
            title="Junk email and spam",
            description="Identify and manage junk email and spam.",
            parent=t7,
            metadata=dict(
                description="Content, questions, or issues related to junk email and spam email.",
            ),
            products=[tb, tba],
        )
        t7_7 = TopicFactory(
            title="Send and receive email",
            description="Everything you need to know about sending and receiving emails.",
            parent=t7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to sending or receiving email (i.e. -"
                    " scheduling emails, filtering recipients, or blocking senders)"
                ),
            ),
            products=[relay, tb, tba],
        )
        TopicFactory(
            title="Email forwarding",
            description="Troubleshoot email forwarding issues.",
            parent=t7_7,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing how Relay forwards messages"
                    " from an email mask to a user's real email."
                ),
            ),
            products=[relay],
        )
        t8 = TopicFactory(
            title="Installation and updates",
            description=(
                "Learn how to install your favorite Mozilla products and keep them updated."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to installing and updating Mozilla's"
                    " products."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, vpn, pocket, tb, tba],
        )
        t8_1 = TopicFactory(
            title="Install",
            description="Learn about how to install Mozilla’s products on your devices.",
            parent=t8,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to installing Mozilla's products."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, vpn, pocket, tb, tba],
        )
        TopicFactory(
            title="ESR",
            description="Troubleshoot ESR issues.",
            parent=t8_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to installing and maintaining the"
                    " Extended Support Release for Firefox (older versions of the browser that are"
                    " maintained and supported for a specific period of time)."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Install failure",
            description="Troubleshoot install failure issues.",
            parent=t8_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to successful app installation."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        t8_2 = TopicFactory(
            title="Update",
            description=(
                "Keep the Mozilla products you use up to date with the latest features and"
                " improvements."
            ),
            parent=t8,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to updating Mozilla's products for the"
                    " latest features and improvements."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, vpn, pocket, tb, tba],
        )
        TopicFactory(
            title="Update failure",
            description="Troubleshoot update failure issues.",
            parent=t8_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to trying to update a Mozilla product's"
                    " app."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        t9 = TopicFactory(
            title="Passwords and sign in",
            description="Manage your passwords and securely access your accounts.",
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing passwords and signing in to"
                    " accounts."
                ),
            ),
            products=[firefox, mobile, ios, relay, mdn, ma, monitor, vpn, pocket, tb, tba],
        )
        TopicFactory(
            title="Primary password",
            description="Set up a primary password to secure your saved passwords.",
            parent=t9,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the Primary Password used to secure"
                    " a user’s saved usernames and passwords."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Reset passwords",
            description="Reset your passwords when you forget them.",
            parent=t9,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to resetting passwords (e.g. - a"
                    " Mozilla Account password) to regain login access."
                ),
            ),
            products=[firefox, mobile, ios, ma, vpn, pocket, tb, tba],
        )
        t9_3 = TopicFactory(
            title="Save passwords",
            description="Save your passwords for easy sign-in.",
            parent=t9,
            metadata=dict(
                description="Content, questions, or issues related to saving passwords.",
            ),
            products=[firefox, mobile, ios, ma, monitor, vpn, tb, tba],
        )
        TopicFactory(
            title="Password autofill",
            description="Troubleshoot password autofill issues.",
            parent=t9_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to saving passwords or automatic input"
                    " of passwords into sign in fields using the autofill feature. Note that this"
                    " topic is unrelated to Mozilla passwords."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Password manager",
            description="Troubleshoot password manager issues.",
            parent=t9_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the Password Manager feature."
                ),
            ),
            products=[firefox, mobile, ios, monitor, vpn],
        )
        t9_4 = TopicFactory(
            title="Sign in",
            description="Sign in to your accounts securely.",
            parent=t9,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to signing into Mozilla's products,"
                    " accounts, or services."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="3rd party sign in",
            description="Troubleshoot 3rd party sign in issues.",
            parent=t9_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to 3rd party authentication methods"
                    " like signing in with a Google or Apple account."
                ),
            ),
            products=[vpn],
        )
        TopicFactory(
            title="Email verify lockout",
            description="Troubleshoot email verify lockout issues.",
            parent=t9_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to being unable to verify their account"
                    " due to being locked out of their email."
                ),
            ),
            products=[vpn],
        )
        TopicFactory(
            title="Sign in failure",
            description="Troubleshoot sign in failure issues.",
            parent=t9_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to users being unable to sign in to"
                    " their account."
                ),
            ),
            products=[vpn],
        )
        t9_5 = TopicFactory(
            title="Two-factor authentication",
            description=(
                "Use two-factor authentication to add an extra layer of security when signing in."
            ),
            parent=t9,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to two-factor or multi-factor"
                    " authentication as an extra layer of security when signing in."
                ),
            ),
            products=[firefox, mobile, ios, ma, vpn],
        )
        TopicFactory(
            title="SMS Recovery",
            description=(
                "Use SMS messages as a method for account recovery and two-factor authentication."
            ),
            parent=t9_5,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to users getting locked out of their"
                    " account during the process of two-factor authentication."
                ),
            ),
            products=[ma],
        )
        t10 = TopicFactory(
            title="Performance and connectivity",
            description=(
                "Deal with error messages, crashing applications, connectivity issues, and slow"
                " performance."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to error messages, crashing"
                    " applications, connectivity issues, and slow performance (i.e. - when a"
                    " Mozilla app does not connect to the internet but other apps do, when sites"
                    " crash for no discernable reason, etc.)"
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, mdn, vpn, pocket, tb, tba],
        )
        t10_1 = TopicFactory(
            title="Connectivity",
            description="Troubleshoot issues with connectivity.",
            parent=t10,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to app or product connectivity (i.e. -"
                    " network connectivity, connecting to services, etc.)."
                ),
            ),
            products=[firefox, mobile, ios, vpn, tb, tba],
        )
        TopicFactory(
            title="Can't select server",
            description="Troubleshoot can't select server issues.",
            parent=t10_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to users being unable to select a"
                    " specific server in Mozilla VPN."
                ),
            ),
            products=[vpn],
        )
        TopicFactory(
            title="Connection failure",
            description="Troubleshoot connection failure issues.",
            parent=t10_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to users being unable to connect to a"
                    " sever in Mozilla VPN."
                ),
            ),
            products=[vpn],
        )
        TopicFactory(
            title="Slow connection",
            description="Troubleshoot slow connection issues.",
            parent=t10_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to slow experiences with Mozilla's"
                    " products or services and internet connectivity."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        t10_2 = TopicFactory(
            title="Crashing and slow performance",
            description="Troubleshoot issues with app crashes or slow performance.",
            parent=t10,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to app crashes or general slow"
                    " performance."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, vpn, pocket, tb, tba],
        )
        TopicFactory(
            title="App crash",
            description="Troubleshoot app crash issues.",
            parent=t10_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the product or app crashing."
                ),
            ),
            products=[firefox, mobile, ios, vpn, tb, tba],
        )
        TopicFactory(
            title="App responsiveness",
            description="Troubleshoot app responsiveness issues.",
            parent=t10_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to experienced slowness and delayed"
                    " responsiveness with an app or product (such as keyboard stuttering, hanging"
                    " or long page loads times, app freezes when opening or closing, etc.)"
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Launch failure",
            description="Troubleshoot launch failure issues.",
            parent=t10_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to failures or crashes when attempting"
                    " to launch a product or app."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Loading speed",
            description="Troubleshoot loading speed issues.",
            parent=t10_2,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to experienced slowness when loading"
                    " websites."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t10_3 = TopicFactory(
            title="Error codes",
            description="Troubleshoot issues with error codes.",
            parent=t10,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to encountered error codes while trying"
                    " to navigate a website."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Web certificates",
            description="Troubleshoot web certificates issues.",
            parent=t10_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to expired web certificate errors while"
                    " trying to navigate a website."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t10_4 = TopicFactory(
            title="Site breakages",
            description="Resolve problems when websites don’t load or function correctly.",
            parent=t10,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to whole, or parts of, websites not"
                    " loading or functioning correctly."
                ),
            ),
            products=[firefox, focus, mobile, ios, vpn],
        )
        TopicFactory(
            title="Blocked application/service/website",
            description="Troubleshoot blocked application/service/website issues.",
            parent=t10_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to blocked applications, services, or"
                    " websites that users are trying to access."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Security software",
            description="Troubleshoot security software issues.",
            parent=t10_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to anti-virus software, firewalls,"
                    " VPNs, and other security software affecting the functionality of a website."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Web compatibility",
            description="Troubleshoot web compatibility issues.",
            parent=t10_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to sites that have been optimized for"
                    " other browsers but not Firefox."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        t11 = TopicFactory(
            title="Privacy and security",
            description="Learn how to protect your privacy and secure your data.",
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to the privacy and security of user"
                    " data in Mozilla's products (i.e. - how Mozilla collects, stores, and uses"
                    " user data, as well as how to delete user data)."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, ma, monitor, vpn, pocket, tb, tba],
        )
        t11_1 = TopicFactory(
            title="Data removal",
            description="Remove your data from Mozilla’s products.",
            parent=t11,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to removing personal data that has been"
                    " exposed or is displayed in non-secure locations online."
                ),
            ),
            products=[monitor],
        )
        TopicFactory(
            title="Data brokers",
            description="Troubleshoot data brokers issues.",
            parent=t11_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to data brokers - individuals or"
                    " companies that specialize in collecting, buying, and/or selling personal"
                    " data online."
                ),
            ),
            products=[monitor],
        )
        TopicFactory(
            title="Privacy scan",
            description="Troubleshoot privacy scan issues.",
            parent=t11_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Monitor's privacy scan feature that"
                    " allows users to determine if their personal information has been exposed"
                    " online."
                ),
            ),
            products=[monitor],
        )
        TopicFactory(
            title="Encryption",
            description="Use encryption features to keep yourself and your data secure.",
            parent=t11,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to  various encryption features like"
                    " HTTPS, ECH, and TLS."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, ma, vpn, tb, tba],
        )
        t11_3 = TopicFactory(
            title="Masking",
            description="Mask your email and phone number to better protect your privacy.",
            parent=t11,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to features and functionality that"
                    " allow a user to hide their actual email or phone number when using them for"
                    " online goods and services."
                ),
            ),
            products=[relay, ma],
        )
        TopicFactory(
            title="Email and phone masking",
            description="Troubleshoot email and phone masking issues.",
            parent=t11_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Relay masks used to hide a user's"
                    " actual email."
                ),
            ),
            products=[relay],
        )
        TopicFactory(
            title="Email masking",
            description="Troubleshoot email masking issues.",
            parent=t11_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Relay masks used to hide a user's"
                    " actual phone number."
                ),
            ),
            products=[relay],
        )
        TopicFactory(
            title="Phone masking",
            description="Troubleshoot phone masking issues.",
            parent=t11_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to bundled features in Relay that hide"
                    " a user's email and phone masking (together instead of separately)."
                ),
            ),
            products=[relay],
        )
        t11_4 = TopicFactory(
            title="Security",
            description="Keep yourself secure online.",
            parent=t11,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to a user's personal data security,"
                    " browser security, etc."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, ma, monitor, vpn, tb, tba],
        )
        TopicFactory(
            title="Browser security",
            description="Troubleshoot browser security issues.",
            parent=t11_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to strategies for browsing securely,"
                    " browser security settings, Firefox's innate privacy prioritization, and"
                    " more."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Device permissions",
            description="Troubleshoot device permissions issues.",
            parent=t11_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to app permissions that grant access to"
                    " parts of a user's device, such as the camera, microphone, and more."
                ),
            ),
            products=[firefox, mobile, ios, relay, vpn],
        )
        t11_5 = TopicFactory(
            title="Tracking protection",
            description="Enable tracking protection to enhance your privacy.",
            parent=t11,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to enabling tracking protection or"
                    " managing tracking protection settings."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, ma, vpn, pocket],
        )
        TopicFactory(
            title="Cookies",
            description="Troubleshoot cookies issues.",
            parent=t11_5,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to tracking concerns around browser"
                    " cookies."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Email trackers",
            description="Troubleshoot email trackers issues.",
            parent=t11_5,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to trackers hidden in links, images, or"
                    " attachments contained in the body of the emails that advertisers and third"
                    " parties use to collect information about users via marketing emails."
                ),
            ),
            products=[relay, vpn],
        )
        t12 = TopicFactory(
            title="Search, tag, and share",
            description=(
                "Learn about search functionality and how to organize or share content in Mozilla"
                " products."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to search functionality and how to"
                    " organize (tagging) or share content."
                ),
            ),
            products=[firefox, focus, mobile, ios, relay, pocket, tb, tba],
        )
        t12_1 = TopicFactory(
            title="Search",
            description="Find information quickly and easily.",
            parent=t12,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to conducting searches in browser,"
                    " searching for content or settings within a product, and general search"
                    " functionality."
                ),
            ),
            products=[firefox, focus, mobile, ios, pocket, tb, tba],
        )
        TopicFactory(
            title="Full text search",
            description="Troubleshoot full text search issues.",
            parent=t12_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to Pocket's premium search feature that"
                    " gives users expanded search functionality, such as searching the entire text"
                    " of an article, searching tags, topics, authors, and more."
                ),
            ),
            products=[pocket],
        )
        TopicFactory(
            title="Search suggestions",
            description="Troubleshoot search suggestions issues.",
            parent=t12_1,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to suggested search terms offered by"
                    " the browser when conducting a search. This topic can also apply specifically"
                    " to the Firefox Suggest feature."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        TopicFactory(
            title="Share content",
            description="Learn how to share links, content, messages, and more.",
            parent=t12,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to sharing content, data, or files like"
                    " links, articles, or images, especially when this is done using the Share"
                    " functionality."
                ),
            ),
            products=[firefox, mobile, ios, pocket],
        )
        t12_3 = TopicFactory(
            title="Tags",
            description="Categorize and organize efficiently with tags.",
            parent=t12,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to tags or tagging functions in"
                    " products (i.e. - tagging saved articles in Pocket, tagging email messages in"
                    " Thunderbird, or tagging masks with labels in Relay)."
                ),
            ),
            products=[relay, pocket, tb, tba],
        )
        TopicFactory(
            title="Mask labels",
            description="Troubleshoot mask labels issues.",
            parent=t12_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to user-created labels for their Relay"
                    " masks."
                ),
            ),
            products=[relay],
        )
        TopicFactory(
            title="Suggested tags",
            description="Troubleshoot suggested tags issues.",
            parent=t12_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to content tags that are suggested by"
                    " Pocket."
                ),
            ),
            products=[pocket],
        )
        t13 = TopicFactory(
            title="Settings",
            description=(
                "Manage and customize your product experience with settings, add-ons, and more."
            ),
            parent=None,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to managing and customizing product"
                    " settings, add-ons, and more."
                ),
            ),
            products=[
                firefox,
                focus,
                mobile,
                ffe,
                ios,
                relay,
                mdn,
                ma,
                monitor,
                vpn,
                pocket,
                tb,
                tba,
            ],
        )
        t13_1 = TopicFactory(
            title="Add-ons, extensions, and themes",
            description="Enhance product functionality with add-ons, extensions, and themes.",
            parent=t13,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to enhancing product functionality with"
                    " add-ons, extensions, and themes."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, ma, vpn, pocket, tb],
        )
        TopicFactory(
            title="Extensions",
            description="Troubleshoot extensions issues.",
            parent=t13_1,
            metadata=dict(
                description=(
                    "Content, questions, requests, or issues related to product extensions"
                    " (add-ons)."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, ma, vpn, pocket, tb],
        )
        TopicFactory(
            title="Themes",
            description="Troubleshoot themes issues.",
            parent=t13_1,
            metadata=dict(
                description="Content, questions, requests, or issues related to product themes.",
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, pocket, tb],
        )
        TopicFactory(
            title="Autofill",
            description="Automatically fill your personal information into form fields and more.",
            parent=t13,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to autofilling settings or personal"
                    " information (i.e. - email, addresses, and payment cards) into form fields"
                    " and more."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, tb, tba],
        )
        t13_3 = TopicFactory(
            title="Customization",
            description="Customize product appearance and functionality to suit your preferences.",
            parent=t13,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to customizing a product's settings and"
                    " functionality."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, mdn, pocket, tb, tba],
        )
        TopicFactory(
            title="Browser appearance",
            description="Troubleshoot browser appearance issues.",
            parent=t13_3,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to customizing the Firefox browser's"
                    " appearance."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        t13_4 = TopicFactory(
            title="Import and export settings",
            description=(
                "Learn how to import and export product settings for easy setup and migration."
            ),
            parent=t13,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to transferring product, account, or"
                    " profile settings across devices, or from one browser to another."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, vpn, tb, tba],
        )
        TopicFactory(
            title="Add device",
            description="Troubleshoot add device issues.",
            parent=t13_4,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to adding a new device to a user's"
                    " account (e.g. - adding a new computer to a user's Mozilla VPN account)."
                ),
            ),
            products=[firefox, mobile, ios, vpn],
        )
        TopicFactory(
            title="Languages",
            description="Change and manage language settings in Mozilla’s products.",
            parent=t13,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to changing and managing languages,"
                    " translations, and locale settings in Mozilla's products."
                ),
            ),
            products=[firefox, focus, mobile, ffe, ios, relay, vpn, tb, tba],
        )
        t13_6 = TopicFactory(
            title="Notifications",
            description="Manage notifications in Mozilla’s products.",
            parent=t13,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to notifications received in app,"
                    " managing notification settings, and more."
                ),
            ),
            products=[firefox, mobile, ios, relay, monitor],
        )
        TopicFactory(
            title="Alerts",
            description="Troubleshoot alerts issues.",
            parent=t13_6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to in-product or in-app alerts."
                ),
            ),
            products=[monitor],
        )
        TopicFactory(
            title="Forwarded message notification",
            description="Troubleshoot forwarded message notification issues.",
            parent=t13_6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related to notifications sent by Relay about"
                    " messages that have been forwarded to a user's real email or phone number."
                ),
            ),
            products=[relay],
        )
        TopicFactory(
            title="Push notifications",
            description="Troubleshoot push notifications issues.",
            parent=t13_6,
            metadata=dict(
                description=(
                    "Content, questions, or issues related specifically to notifications pushed to"
                    " a user's device from a Mozilla app."
                ),
            ),
            products=[firefox, mobile, ios],
        )
        self.topic_undefined = TopicFactory(
            title="Undefined",
            description="A topic that can be applied to content that is spam or non-actionable",
            parent=None,
            metadata=dict(
                description=(
                    "A topic that can be applied to content that is spam or non-actionable"
                ),
            ),
            products=[
                firefox,
                focus,
                mobile,
                ffe,
                ios,
                relay,
                mdn,
                ma,
                monitor,
                vpn,
                pocket,
                tb,
                tba,
            ],
        )

    def test_spam_1(self):
        question = QuestionFactory(
            product=self.firefox,
            content=(
                "Get rich with cryptocurrencies! Call this toll-free number 1-800-999-9999 today!"
            ),
        )

        content_type = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertIsNone(question.topic)
        self.assertFalse(
            FlaggedObject.objects.filter(object_id=question.id, content_type=content_type).exists()
        )

        classify(question)

        question.refresh_from_db()

        self.assertTrue(question.is_spam)
        self.assertEqual(question.topic, self.topic_undefined)
        self.assertTrue(
            FlaggedObject.objects.filter(
                creator=self.sumo_bot,
                object_id=question.id,
                content_type=content_type,
                reason=FlaggedObject.REASON_SPAM,
                status=FlaggedObject.FLAG_PENDING,
                notes__startswith=(
                    "Automatically flagged and marked as spam for the following reason:"
                ),
            ).exists()
        )

    def test_topic_1(self):
        question = QuestionFactory(
            product=self.firefox,
            content="How do I make my tabs vertical rather than horizontal?",
        )

        content_type = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertIsNone(question.topic)
        self.assertFalse(
            FlaggedObject.objects.filter(object_id=question.id, content_type=content_type).exists()
        )

        classify(question)

        question.refresh_from_db()

        self.assertFalse(question.is_spam)
        self.assertFalse(
            FlaggedObject.objects.filter(object_id=question.id, content_type=content_type).exists()
        )
        self.assertEqual(question.topic, self.tabs)

    def test_topic_2(self):
        question = QuestionFactory(
            product=self.firefox,
            content=(
                "I just bought a new computer and installed Firefox, but I don't know how"
                " to get my old bookmarks and other settings. Help!"
            ),
        )

        content_type = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertIsNone(question.topic)
        self.assertFalse(
            FlaggedObject.objects.filter(object_id=question.id, content_type=content_type).exists()
        )

        classify(question)

        question.refresh_from_db()

        self.assertFalse(question.is_spam)
        self.assertFalse(
            FlaggedObject.objects.filter(object_id=question.id, content_type=content_type).exists()
        )
        self.assertEqual(question.topic, self.sync_data)
