=========
Questions
=========

This document explains what kinds of question states exist in Kitsune,
how they are set and their implications.


Configuring new products
========================

To configure a new product for AAQ you must edit ``config.py`` within the questions app.

First, ensure the ``Product`` object exists for this product in the products app.If not create a new
``Product``.

Next, Add a new item to the ``products`` dictionary using something like::

    ('product-slug', {
        'name': _lazy(u'Product Name'),
        'subtitle': _lazy('A brief description'),
        'extra_fields': [],
        'tags': ['tag-slug'],
        'product': 'product-slug',
        'categories': SortedDict([
            ('topic-slug', {
                'name': _lazy(u'Topic name'),
                'topic': 'topic-slug',
                'tags': []
            }),
        ])
    }),

``'product-slug'`` should be the slug of the ``Product`` object for this product.

You will also need to add a new 96x96 icon to the ``img/logos.large.sprite.png`` and
will need to update the ``.logo-sprite`` class in ``questions.less`` to account for the new logo.

The same changes will need to be made to ``img/mobile/logos-sprite-2x.png`` and a
non-retina (half size) version ``img/mobile/logos-sprite.png``. Finally update the
``.logo-sprite`` class in ``mobile/main.less``.


Question States
===============

Not yet posted
--------------
Questions are created within the `Ask a question` workflow,
but they are not shown in question listings until the user is confirmed.
With Persona for authentication this status is impossible,
since email addresses are confirmed right away.


Default
-------
This is the unmarked state of the thread.

Implications:

* Users can reply
* Visible in regular SUMO searches (with at least one helpful reply)
* Visible to external searches
* Visible in the regular questions list
* Visible in the `related threads` section


Locked
------
This is the locked state of a thread. A thread can be locked in two ways:

* By manually locking it via the question UI
* Automatically after 180 days.

Implications:

* Users can't reply
* Moderators can unlock to reply
* If there is an answer, the locked thread is still shown by search engines
  and our internal search.
* If there is no answer, the locked thread will not be shown by search
  engines and our internal search.


Not indexed
-----------
Questions with no answers that are older than 30 days have a meta tag
telling search engines not to show them.
