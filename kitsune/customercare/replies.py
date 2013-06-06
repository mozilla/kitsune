from django.conf import settings

from pyquery import PyQuery

from kitsune.wiki.models import Document


REPLIES_DOCUMENT_SLUG = 'army-of-awesome-common-replies'


def get_common_replies(locale=settings.WIKI_DEFAULT_LANGUAGE):
    """Returns the common replies.

    Parses the KB article with the replies puts them in a list of dicts.

    The KB article should have the following wiki syntax structure::

        =Category 1=

        ==Reply 1==
        Reply goes here http://example.com/kb-article

        ==Reply 2==
        Another reply here

        =Category 2=
        ==Reply 3==
        And another reply


    Which results in the following HTML::

        <h1 id="w_category-1">Category 1</h1>
        <h2 id="w_snippet-1">Reply 1</h2>
        <p>Reply goes here <a href="http://example.com/kb-article">
        http://example.com/kb-article</a>
        </p>
        <h2 id="w_snippet-2">Reply 2</h2>
        <p>Another reply here
        </p>
        <h1 id="w_category-2">Category 2</h1>
        <h2 id="w_snippet-3">Reply 3</h2>
        <p>And another reply
        </p>


    The resulting list returned would be::

        [{'title': 'Category 1',
          'responses':
            [{'title': 'Reply 1',
              'response': 'Reply goes here http://example.com/kb-article'},
             {'title': 'Reply 2',
              'response': 'Another reply here'}]
         },
         {'title': 'Category 2',
          'responses':
            [{'title': 'Reply 3',
              'response': 'And another reply'}]
         }]

    """
    replies = []

    # Get the replies document in the right locale, if available.
    try:
        default_doc = Document.objects.get(
            slug=REPLIES_DOCUMENT_SLUG,
            locale=settings.WIKI_DEFAULT_LANGUAGE)
    except Document.DoesNotExist:
        return replies

    if locale != default_doc.locale:
        translated_doc = default_doc.translated_to(locale)
        if translated_doc and translated_doc.current_revision:
            doc = translated_doc
        else:
            doc = default_doc
    else:
        doc = default_doc

    # Parse the document HTML into responses.
    pq = PyQuery(doc.html)

    # Start at the first h1 and traverse down from there.
    try:
        current_node = pq('h1')[0]
    except IndexError:
        return replies

    current_category = None
    current_response = None
    while current_node is not None:
        if current_node.tag == 'h1':
            # New category.
            current_category = {
                'title': current_node.text,
                'responses': []}
            replies.append(current_category)
        elif current_node.tag == 'h2':
            # New response.
            current_response = {
                'title': current_node.text,
                'response': ''}
            current_category['responses'].append(current_response)
        elif current_node.tag == 'p':
            # The text for a response.
            text = current_node.text_content().strip()
            if text and current_response:
                current_response['response'] = text

        # Ignore any other tags that come through.

        current_node = current_node.getnext()

    return replies
