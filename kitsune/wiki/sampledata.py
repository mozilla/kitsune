import os

from datetime import datetime

from kitsune.products.models import Product, Topic
from kitsune.products.tests import TopicFactory
from kitsune.wiki.tests import DocumentFactory, RevisionFactory, ApprovedRevisionFactory


def read_file(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return open(os.path.join(data_dir, filename), 'r').read()


FLASH_CONTENT = read_file('FlashCrashes.wiki')


def generate_sampledata(options):
    # There are two products in our schema
    try:
        firefox = Product.objects.get(slug='firefox')
    except Product.DoesNotExist:
        # Note: This matches migration 156. When run in the tests, the
        # migrations don't happen.
        firefox = Product(title='Firefox',
                          description='Web browser for Windows, Mac and Linux',
                          display_order=1,
                          visible=True,
                          slug='firefox')
        firefox.save()

    try:
        mobile = Product.objects.get(slug='mobile')
    except Product.DoesNotExist:
        # Note: This matches migration 156. When run in the tests, the
        # migrations don't happen.
        mobile = Product(
            title='Firefox for Android',
            description='Web browser for Android smartphones and tablets',
            display_order=2,
            visible=True,
            slug='mobile')
        mobile.save()

    for p in [firefox, mobile]:
        # Create the top 10 topics used
        TopicFactory(
            product=p,
            title='Learn the Basics: get started',
            slug='get-started')
        TopicFactory(
            product=p,
            title='Download, install and migration',
            slug='download-and-install')
        TopicFactory(
            product=p,
            title='Privacy and security settings',
            slug='privacy-and-security')
        TopicFactory(
            product=p,
            title='Customize controls, options and add-ons',
            slug='customize')
        TopicFactory(
            product=p,
            title='Fix slowness, crashing, error messages and other problems',
            slug='fix-problems')
        TopicFactory(product=p, title='Tips and tricks', slug='tips')
        TopicFactory(product=p, title='Bookmarks', slug='bookmarks')
        TopicFactory(product=p, title='Cookies', slug='cookies')
        TopicFactory(product=p, title='Tabs', slug='tabs')
        TopicFactory(product=p, title='Websites', slug='websites')
        TopicFactory(product=p, title='Other', slug='other')

        # 'hot' topic is created by a migration. Check for it's existence
        # before creating a new one.
        if not Topic.objects.filter(product=p, slug='hot').exists():
            TopicFactory(product=p, title='Hot topics', slug='hot')

    # Create a hot article
    flash = DocumentFactory(title='Flash 11.3 crashes', slug='flash-113-crashes')
    RevisionFactory(
        content=FLASH_CONTENT,
        document=flash,
        is_approved=True,
        reviewed=datetime.now())
    flash.products.add(firefox)
    flash.topics.add(Topic.objects.get(product=firefox, slug='fix-problems'))
    flash.topics.add(Topic.objects.get(product=firefox, slug='hot'))

    # Generate 9 sample documents with 2 topics each
    topics = list(Topic.objects.all())
    for i in range(9):
        d = DocumentFactory(title='Sample Article %s' % str(i + 1),
                            slug='sample-article-%s' % str(i + 1))
        RevisionFactory(document=d, is_approved=True, reviewed=datetime.now())
        d.products.add(firefox)
        d.products.add(mobile)
        d.topics.add(topics[i])
        d.topics.add(topics[i + 11])

        ApprovedRevisionFactory(
            document__products=[firefox, mobile],
            document__topics=[topics[i], topics[i + 1]])
