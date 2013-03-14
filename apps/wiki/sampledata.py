import os

from datetime import datetime

from products.models import Product
from topics.models import Topic
from topics.tests import topic
from wiki.tests import document, revision


def read_file(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return open(os.path.join(data_dir, filename), 'r').read()


MOZILLA_NEWS_CONTENT = read_file('MozillaNews.wiki')
SUGGESTION_BOX_CONTENT = read_file('SuggestionBox.wiki')
SUPERHEROES_CONTENT = read_file('SuperheroesWanted.wiki')
COMMUNITY_CONTENT = read_file('GetCommunitySupport.wiki')
FLASH_CONTENT = read_file('FlashCrashes.wiki')


def generate_sampledata(options):
    # Create the top 10 topics used
    topic(title='Learn the Basics: get started', slug='get-started',
          save=True)
    topic(title='Download, install and migration',
          slug='download-and-install', save=True)
    topic(title='Privacy and security settings', slug='privacy-and-security',
          save=True)
    topic(title='Customize controls, options and add-ons', slug='customize',
          save=True)
    topic(title='Fix slowness, crashing, error messages and other problems',
          slug='fix-problems', save=True)
    topic(title='Tips and tricks', slug='tips', save=True)
    topic(title='Bookmarks', slug='bookmarks', save=True)
    topic(title='Cookies', slug='cookies', save=True)
    topic(title='Tabs', slug='tabs', save=True)
    topic(title='Websites', slug='websites', save=True)
    topic(title='Hot topics', slug='hot', save=True)

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
        mobile = Product(title='Firefox for Mobile',
                         description='Web browser for Android smartphones and tablets',
                         display_order=2,
                         visible=True,
                         slug='mobile')
        mobile.save()

    # Create the special documents that are linked to from the home page
    moznews = document(title='Mozilla News', slug='mozilla-news', save=True)
    revision(content=MOZILLA_NEWS_CONTENT, document=moznews, is_approved=True,
             reviewed=datetime.now(), save=True)
    suggestion = document(title='Suggestion Box', slug='suggestion-box',
                          save=True)
    revision(content=SUGGESTION_BOX_CONTENT, document=suggestion,
             is_approved=True, reviewed=datetime.now(), save=True)
    community = document(title='Get community support',
                         slug='get-community-support', save=True)
    revision(content=COMMUNITY_CONTENT, document=community,
             is_approved=True, reviewed=datetime.now(), save=True)

    # Create a hot article
    flash = document(title='Flash 11.3 crashes', slug='flash-113-crashes',
                     save=True)
    revision(content=FLASH_CONTENT, document=flash, is_approved=True,
             reviewed=datetime.now(), save=True)
    flash.products.add(firefox)
    flash.topics.add(Topic.objects.get(slug='fix-problems'))
    flash.topics.add(Topic.objects.get(slug='hot'))

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
        d.topics.add(topics[i + 1])
