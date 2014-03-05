import os

from datetime import datetime

from kitsune.products.models import Product, Topic
from kitsune.products.tests import topic
from kitsune.wiki.tests import document, revision


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
            title='Firefox for Mobile',
            description='Web browser for Android smartphones and tablets',
            display_order=2,
            visible=True,
            slug='mobile')
        mobile.save()

    for p in [firefox, mobile]:
        # Create the top 10 topics used
        topic(
            product=p,
            title='Learn the Basics: get started',
            slug='get-started',
            save=True)
        topic(
            product=p,
            title='Download, install and migration',
            slug='download-and-install',
            save=True)
        topic(
            product=p,
            title='Privacy and security settings',
            slug='privacy-and-security',
            save=True)
        topic(
            product=p,
            title='Customize controls, options and add-ons',
            slug='customize',
            save=True)
        topic(
            product=p,
            title='Fix slowness, crashing, error messages and other problems',
            slug='fix-problems',
            save=True)
        topic(product=p, title='Tips and tricks', slug='tips', save=True)
        topic(product=p, title='Bookmarks', slug='bookmarks', save=True)
        topic(product=p, title='Cookies', slug='cookies', save=True)
        topic(product=p, title='Tabs', slug='tabs', save=True)
        topic(product=p, title='Websites', slug='websites', save=True)
        topic(product=p, title='Other', slug='other', save=True)

        # 'hot' topic is created by a migration. Check for it's existence
        # before creating a new one.
        if not Topic.objects.filter(product=p, slug='hot').exists():
            topic(product=p, title='Hot topics', slug='hot', save=True)

    # Create a hot article
    flash = document(title='Flash 11.3 crashes', slug='flash-113-crashes',
                     save=True)
    revision(content=FLASH_CONTENT, document=flash, is_approved=True,
             reviewed=datetime.now(), save=True)
    flash.products.add(firefox)
    flash.topics.add(Topic.objects.get(product=firefox, slug='fix-problems'))
    flash.topics.add(Topic.objects.get(product=firefox, slug='hot'))

    # Generate 9 sample documents with 2 topics each
    topics = list(Topic.objects.all())
    for i in xrange(9):
        d = document(title='Sample Article %s' % str(i + 1),
                     slug='sample-article-%s' % str(i + 1), save=True)
        revision(document=d, is_approved=True, reviewed=datetime.now(),
                 save=True)
        d.products.add(firefox)
        d.products.add(mobile)
        d.topics.add(topics[i])
        d.topics.add(topics[i + 11])
