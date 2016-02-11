# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class MockArticle(dict):

    def __init__(self, suffix="", **kwargs):
        # set default values
        import time
        timestamp = repr(time.time()).replace('.', '')

        self['title'] = "test_article_%s%s" % (timestamp, suffix)
        self['slug'] = self['title']
        self['category'] = "How to"
        self['keyword'] = "test"
        self['summary'] = "this is an automated summary_%s%s" % (timestamp, suffix)
        self['content'] = "automated content_%s%s" % (timestamp, suffix)
        self['comment'] = "comment %s %s" % (timestamp, suffix)
        self['product'] = "Firefox"

        # update with any keyword arguments passed
        self.update(**kwargs)
