import sys


class MigrationStatusPrinter(object):
    """
    Print migration status in an attractive way during a Django migration run.

    In particular, you get output that looks like this

        Running migrations:
          Applying users.0005_set_initial_contrib_email_flag...
            set first_l10n_email_sent on 2793 profiles.
            set first_answer_email_sent on 46863 profiles.
            OK

    Each step that wants to use this class should make its own instance.
    Reusing instances will not result in the right print behavior.
    """

    def __init__(self):
        self.printed_yet = False

    def info(self, msg, *args, **kwargs):
        if 'test' in sys.argv:
            return

        if not self.printed_yet:
            print('\n   ', end='')
            self.printed_yet = True
        msg = msg.format(*args, **kwargs)
        print(' {0}'.format(msg), end='\n   ')
