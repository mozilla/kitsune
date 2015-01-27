Notifications
=============

Notifications in SUMO are an extension of the ideas in
`django-activity-stream <https://github.com/justquick/django-activity-stream>`_.
The package name for which is ``actstream``.

There are three primary kinds of objects: ``actstream.models.Action``,
``actstream.models.Follow`` and ``kitsune.notifications.models.Notification``.

Action
------

In theory, one Action is created anytime something happens that someone might
want to be notified about. In practice, not everything will have actions right
away, but these will be added over time.

Actions have a few important fields:

* ``timestamp`` - When the action happened.
* ``actor`` - All actions have an actor. This is generally the user that performed
  an action. Internally this is a ContentTypes GenericForeignKey, so it could
  point to any object.
* ``verb`` - This is a string representing what the user did. Things like "asked",
  "created", or "edited" are appropriate.
* ``action_object`` (optional) - This is the object that was acted with. If an
  object was created, this is the created object. This might not always be
  applicable. Internally this is a ContentTypes GenericForeignKey.
* ``target`` (optional) - This is the place the action happened. If the object
  created belongs to a group, this might be the group. Internally this is a
  ContentTypes GenericForeignKey.

Examples
~~~~~~~~

If Bob creates a question, an action will be created with these properties::

  action(bob, verb='asked', action_object=the_new_question)

Since questions don't belong to a larger group, there is no Target.

If Sarah comes along and answers Bob's question, an action will be created
with these properties::

  action(sarah, verb='answered', action_object=the_new_answer, target=the_question)

Since Answers are groups together in relation to a Question, the target should
be the Question in question.

Follow
------

A Follow object represents the desire of one user to be alerted about a class
of Actions. They have three important fields:

* ``user`` - The user that will be notified.
* ``follow_object`` - The object being followed.
* ``actor_only`` (default True) - If actions that involve ``follow_object``, but
  where ``follow_object`` is not ``action.actor`` should notify ``user``.

A user will be alerted about an action if any of these properties are true:

* ``action.actor == follow.follow_object``
* ``action.action_object == follow.follow_object and not follow.actor_only``
* ``action.target == follow.follow_object and not follow.actor_only``

Examples
~~~~~~~~

In the question above, Bob was automatically registered as following the
Question with an ``actor_only = False`` Follow object. So when Sarah answers
the question, generating the action

::

  action(sarah, verb='answered', action_object=the_new_answer, target=the_question)

Bob will be notified, because ``target`` matches the ``action_object`` of one
of his Follow objects.

It will be common for users to follow objects like this. It will be uncommon
for users to follow other users, and in fact at this time there are no use
cases for users following users.


Notification
------------

When an Action is created, not much happens. It goes in the database, and there
may be some sort of activity stream that displays it, but that's it. For a user
to actually be alerted to the Action, a Notification object must be created.
The mechanism that decided if Notification object is created is actstream's
Follow mechanism. More on that below.

When an Action is created, a hook fires. The hook gets a list of users that
are following something that applies to the Action. For every applicable user,
the hook creates a Notification object.

Notifications have only a few properties:

* ``action`` - The associated action.
* ``owner`` - The associated user.
* ``read_at`` - The datetime the user read the notification (or None).
* ``is_read`` (calculated field) - Boolean calculated from ``read_at``.

Notifications also don't have any direct alerting properties, but they are used
by other systems to alert users in some way.
