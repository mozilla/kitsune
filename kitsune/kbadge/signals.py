# Pruned version of django-badger/badger/signals.py
# https://github.com/mozilla/django-badger/blob/master/badger/signals.py

"""
Signals relating to badges.

For each of these, you can register to receive them using standard
Django methods.

Let's look at :py:func:`kitsune.kbadge.signals.badge_will_be_awarded`. For
example::

    from kitsune.kbadge.signals import badge_will_be_awarded

    @receiver(badge_will_be_awarded)
    def my_callback(sender, **kwargs):
        award = kwargs['award']

        print('sender: {0}'.format(sender))
        print('award: {0}'.format(award))


The sender will be :py:class:`badges.models.Award` class. The
``award`` argument will be the ``Award`` instance that is being
awarded.

"""
from django.dispatch import Signal


def _signal_with_docs(args, doc):
    # FIXME - this fixes the docstring, but not the provided arguments
    # so the API docs look weird.
    signal = Signal(providing_args=args)
    signal.__doc__ = doc
    return signal


badge_was_awarded = _signal_with_docs(
    ["award"],
    """Fires off after badge is awarded

    Signal receiver parameters:

    :arg award: the Award instance

    """,
)

badge_will_be_awarded = _signal_with_docs(
    ["award"],
    """Fires off before badge is awarded

    Signal receiver parameters:

    :arg award: the Award instance

    """,
)
