from django.utils.encoding import smart_str

from kitsune.taggit.models import Tag
from kitsune.topics.models import Topic
from kitsune.wiki.models import Document

tags_to_migrate = {
    # '<source tag>': '<destination tag>',
    'sync': 'sync',
    'general': 'general',
    'recovery-key': 'recovery-key',
    'privacy-security': 'privacy-and-security',
    'marketplace': 'marketplace',
    'download-and-install': 'download-and-install',
    'privacy-and-security': 'privacy-and-security',
    'getting-started': 'getting-started',
    'customize': 'customize',
    'addons': 'addons',
    'settings': 'settings',
    'controls': 'controls',
    'flash': 'flash',
    'search': 'search',
    'add-ons': 'addons',
    'tabs': 'tabs',
    'bookmarks': 'bookmarks',
    'tips': 'tips',
    'ios': 'ios',
    'websites': 'websites',
    'persona': 'persona',
    'error-messages': 'error-messages',
    'diagnostics': 'diagnostics',
    'cookies': 'cookies',
    'accessibility': 'accessibility',
    'migrate': 'migrate',
    'android': 'android',
    'history': 'history',
    'slowness-or-hanging': 'slowness-or-hanging',
    'crashing': 'crashing',
    'malware': 'malware',
    'slowness-and-hanging': 'slowness-or-hanging',
    'hanging-and-slowness': 'slowness-or-hanging',
    'profiles': 'profiles',
    'versions': 'versions',
    'download': 'download',
    'dignostics': 'diagnostics',
    'browserid': 'browserid',
    'passwords': 'passwords',
    'profile': 'profiles',
    'security-and-privacy': 'privacy-and-security',
    'diagnostic': 'diagnostics',
}

def run():
    # Get all the tags to migrate.
    tags = Tag.objects.filter(slug__in=tags_to_migrate.keys())

    # For each tag, get the document and add a topic for it.
    for tag in tags:
        try:
            destination_tag = Tag.objects.get(slug=tags_to_migrate[tag.slug])
        except Tag.DoesNotExist:
            print 'Skipped tag %s' % tag
            continue

        # Get or create the topic.
        topic, created = Topic.objects.get_or_create(
            title=destination_tag.name,
            slug=destination_tag.slug,
            display_order=0,
            visible=True)

        if created:
            print 'Created new topic "%s"' % smart_str(topic.slug)

        # Assign the topic to all the documents tagged with tag.
        for doc in Document.objects.filter(tags__slug=tag.slug):
            doc.topics.add(topic)
            print 'Added topic "%s" to document "%s"' % (
                smart_str(topic.slug), smart_str(doc.title))

    print 'Done!'
