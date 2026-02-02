import os

from django.utils import timezone

from kitsune.products.models import Product, Topic
from kitsune.products.tests import TopicFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory, RevisionFactory


def read_file(filename):
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    return open(os.path.join(data_dir, filename)).read()


FLASH_CONTENT = read_file("FlashCrashes.wiki")


def generate_sampledata(options):
    # There are two products in our schema
    try:
        firefox = Product.active.get(slug="firefox")
    except Product.DoesNotExist:
        # Note: This matches migration 156. When run in the tests, the
        # migrations don't happen.
        firefox = Product(
            title="Firefox",
            description="Web browser for Windows, Mac and Linux",
            display_order=1,
            visible=True,
            slug="firefox",
        )
        firefox.save()

    try:
        mobile = Product.active.get(slug="mobile")
    except Product.DoesNotExist:
        # Note: This matches migration 156. When run in the tests, the
        # migrations don't happen.
        mobile = Product(
            title="Firefox for Android",
            description="Web browser for Android smartphones and tablets",
            display_order=2,
            visible=True,
            slug="mobile",
        )
        mobile.save()

    for p in [firefox, mobile]:
        # Create the top 10 topics used
        TopicFactory(products=[p], title="Learn the Basics: get started", slug="get-started")
        TopicFactory(
            products=[p], title="Download, install and migration", slug="download-and-install"
        )
        TopicFactory(
            products=[p], title="Privacy and security settings", slug="privacy-and-security"
        )
        TopicFactory(
            products=[p], title="Customize controls, options and add-ons", slug="customize"
        )
        TopicFactory(
            products=[p],
            title="Fix slowness, crashing, error messages and other problems",
            slug="fix-problems",
        )
        TopicFactory(products=[p], title="Tips and tricks", slug="tips")
        TopicFactory(products=[p], title="Bookmarks", slug="bookmarks")
        TopicFactory(products=[p], title="Cookies", slug="cookies")
        TopicFactory(products=[p], title="Tabs", slug="tabs")
        TopicFactory(products=[p], title="Websites", slug="websites")
        TopicFactory(products=[p], title="Other", slug="other")

        # 'hot' topic is created by a migration. Check for it's existence
        # before creating a new one.
        if not Topic.active.filter(products=p, slug="hot").exists():
            TopicFactory(products=[p], title="Hot topics", slug="hot")

    # Create a hot article
    flash = DocumentFactory(title="Flash 11.3 crashes", slug="flash-113-crashes")
    RevisionFactory(
        content=FLASH_CONTENT, document=flash, is_approved=True, reviewed=timezone.now()
    )
    flash.products.add(firefox)
    flash.topics.add(Topic.active.get(products=firefox, slug="fix-problems"))
    flash.topics.add(Topic.active.get(products=firefox, slug="hot"))

    # Generate 9 sample documents with 2 topics each
    topics = list(Topic.active.all())
    for i in range(9):
        d = DocumentFactory(
            title="Sample Article {}".format(str(i + 1)), slug="sample-article-{}".format(str(i + 1))
        )
        RevisionFactory(document=d, is_approved=True, reviewed=timezone.now())
        d.products.add(firefox)
        d.products.add(mobile)
        d.topics.add(topics[i])
        d.topics.add(topics[i + 11])

        ApprovedRevisionFactory(
            document__products=[firefox, mobile], document__topics=[topics[i], topics[i + 1]]
        )
