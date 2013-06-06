================
Logging Activity
================

The **activity** app provides a way to log arbitrary activity for interested
users (c.f. your Github dashboard). This activity can appear on a user's
profile, on their personal dashboard, or other places.


Logging What Now?
=================

Each bit of activity is represented in the database by an ``Action`` object.
It's linked to relevant users by a ``ManyToManyField``. To add a new action to
users' activity logs, create a new ``Action`` object and add the relevant users
to the ``action.users`` manager.


Formatting Actions
==================

``Action`` objects require a **formatter** class that determines how to render
the action in the log. For example, a formatter for a forum reply might decide
to render the title of the action like this::

    _('{user} replied to {thread}').format(user=, thread=)

Formatters have access to the entire action object, so they can look at any
attached objects including, potentially, the creator (of the action), or the
relevant content object (a ``GenericForeignKey``).

Formatters should probably subclass ``activity.ActionFormatter``, though that's
not strictly required at the moment. They need to accept an ``Action`` object
to their constructors and implement the following properties:

``title``:
  a title for the action
``content``:
  text content, may be blank
``__unicode__()``:
  probably the same as ``title``

An fuller example::

    class ForumReplyFormatter(ActionFormatter):
        def __init__(self, action):
            self.action = action
            self.post = action.content_object
            title = _('{user} replied to {thread}')
            self.title = title.format(user=action.creator,
                                      thread=self.post.thread.title)
            self.content = self.post.content[0:225]

        def __unicode__(self):
            return self.title


Saving the Formatter
--------------------

When creating an ``Action``, you need to save a Python route to a formatter
class. For example, assuming the formatter above was in ``forums.tasks``, you
might store::

    action = Action()
    action.formatter = 'forums.tasks.ForumReplyFormatter'

It should be a path you can import from the Django shell.
