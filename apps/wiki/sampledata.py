from datetime import datetime

from products.models import Product
from topics.models import Topic
from topics.tests import topic
from wiki.tests import document, revision


MOZILLA_NEWS_CONTENT = """
*[https://blog.mozilla.org/security/2012/08/28/protecting-users-against-java-security-vulnerability/ Protecting Users Against Java Security Vulnerability]
*[https://blog.mozilla.org/blog/2012/08/28/firefox-for-android-gets-speedy-and-powerful-upgrade-for-tablets/ Firefox for Android Gets Speedy and Powerful Upgrade for Tablets]
* [https://blog.mozilla.org/blog/2012/07/26/firefox-add-ons-cross-more-than-3-billion-downloads/ Firefox Add-ons Cross More Than 3 Billion Downloads!]
"""

SUGGESTION_BOX_CONTENT = """
=We want your feedback!=
We collect your ratings, read your comments and present them to the Mozilla engineering and products teams every week. Use this link to send us your valuable feedback:
:{button [http://input.mozilla.org/feedback/ Submit Your Feedback]}

==You can also help us make Firefox better by sending us performance data==
*[[Send performance data to Mozilla to help improve Firefox|Send Firefox data]]
*[[How can I help by submitting mobile performance data?|Send Firefox for Android data]]
"""

SUPERHEROES_CONTENT = """
<section>
Congratulations on passing the first test and getting to this page. You are only two small steps away from joining the ranks of our amazing volunteer support community dedicated to helping people get the most out of Firefox. All that's left to do is to create an account and pick a way to get involved.
</section>
"""

COMMUNITY_CONTENT = """
=Ask a question in the community support forum=
Ask a question in the support forum using the link below. You will be taken through a series of pages to determine the product and topic of your question, so our team of expert contributors can get the right person to help you. Note that you'll need to register on the site at the end of the series of pages, but it will all be worth it!<br>

[/en-US/questions/new Ask a Question]

=Additional resources=
You might want to refer to the following additional resources before asking a question in the support forum. Most questions already have been solved by our knowledge base or our team of expert contributors.
*[/questions?filter=solved&sort=requested Frequently asked questions about Mozilla software]
*[https://wiki.mozilla.org Look for an answer in the Mozilla wiki]
*[http://www.mozilla.org/about/forums/ Mozilla support newsgroups]
*[http://forums.mozillazine.org MozillaZine forums]
"""

FLASH_CONTENT = """
Flash 11.3 crashes more frequently than previous versions of Flash. Updating to the latest version of Flash should fix this issue for most people.

__TOC__

=Solution 1: Update Flash =
lorem ipsum dolor

=Solution 2: Downgrade to Flash 10.3=
sit amet

== Step 1: Uninstall Flash ==
lorem ipsum dolor

== Step 2: Install Flash 10.3 ==
sit amet
"""


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

    # There are two products in our schema
    firefox = Product.objects.get(slug='firefox')
    mobile = Product.objects.get(slug='mobile')

    # Create the special documents that are linked to from the home page
    moznews = document(title='Mozilla News', slug='mozilla-news', save=True)
    revision(content=MOZILLA_NEWS_CONTENT, document=moznews, is_approved=True,
             reviewed=datetime.now(), save=True)
    suggestion = document(title='Suggestion Box', slug='suggestion-box',
                          save=True)
    revision(content=SUGGESTION_BOX_CONTENT, document=suggestion,
             is_approved=True, reviewed=datetime.now(), save=True)
    superheroes = document(title='Superheroes Wanted!',
                           slug='superheroes-wanted', save=True)
    revision(content=SUPERHEROES_CONTENT, document=superheroes,
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
        d = document(title='Sample Article %s' % i + 1,
                     slug='sample-article-%s' % i + 1, save=True)
        revision(document=d, is_approved=True, reviewed=datetime.now(),
                 save=True)
        d.products.add(firefox)
        d.products.add(mobile)
        d.topics.add(topics[i])
        d.topics.add(topics[i + 1])
