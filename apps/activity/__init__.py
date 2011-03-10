class ActionFormatter(object):
    """A base class for action formatters.

    Subclasses must implement all properties, optionally with @property."""

    title = 'Something Happened!'
    content = ''

    def __init__(self, action):
        self.action = action

    def __unicode__(self):
        return self.title
