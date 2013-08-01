# -*- coding: utf-8 -*-
from __future__ import division

import math
import string
import re


_whitespace_regex = re.compile(r'\s|-', flags=re.U)
_alpha_regex = re.compile(r'\w', flags=re.U)


def find_word_locations_with_spaces(s):
    """Builds an index in the format of {word: location}.

    This is a english like search. For languages without spaces to
    separate words, use find_word_locations_without_spaces.
    """
    s = s.lower()
    words = [u'']
    for c in s:
        if (_whitespace_regex.match(c) or
            c in string.punctuation and c not in '.!?'):
            words.append(u'')
        elif c in '.!?':  # We want to treat . as a big stop. Add two space.
            words.append(u'')
            words.append(u'')
        elif c in '\'"[]1234567890/\\()_':
            continue
        elif _alpha_regex.match(c) is not None:
            words[-1] += c
        else:
            # characters that we don't care about such as a control character.
            # It's okay if we skip it.
            continue

    locations = {}
    for i, w in enumerate(words):
        if w:
            locations.setdefault(w, []).append(i)

    return locations


def find_word_locations_without_spaces(s):
    """Builds an index of the format of {word: location}.

    This method is for languages like Chinese where there is no spaces
    to denote the beginning and end of a word.
    """
    words = [u'']
    for c in s:
        # Yes, east asian languages could still have white space.
        if _whitespace_regex.match(c) or c in u"；：，、" + string.punctuation:
            words.append(u'')
        # This is at least the punctuations in Chinese.
        elif c in u'。！？':
            words.append(u'')
            words.append(u'')
        elif c in u'\'"[]1234567890/\\()_（）【】『』、￥《》’‘”“':
            continue
        elif _alpha_regex.match(c) is not None:
            words.append(c)
        else:
            continue  # Something weird, but it is totally okay

    locations = {}
    for i, w in enumerate(words):
        if w:
            locations.setdefault(w, []).append(i)
    return locations


# Location based index is not enabled as it is not implemented on the client
# side. It is also not proven that it will work effectively (although later on
# we might need to implement this).
# class LocationIndex(object):
#     def __init__(self):
#         self.index = {}

#     def feed(self, doc_id, texts, get_locations):
#         for text, boost in texts:
#             locations = get_locations(text)
#             for w, l in locations.iteritems():
#                 global_word_locations = self.index.setdefault(w, {})
#                 local_location = global_word_locations.setdefault(doc_id, [])
#                 for location in l:
#                     local_location.append(location)

#     def offline_index(self):
#         return self.index


class TFIDFIndex(object):
    """This is an index for search and ranking based on TF-IDF.

    TF-IDF (Term Frequency - Inverse Document Frequency) is a relatively
    simple and intuitive NLP technique that scores words in a document
    given a corpus based on how important this word is.

    A full explanation of this is provided at <insert url when ready>.
    """
    def __init__(self):
        self.doc_count = 0
        self.global_word_freq = {}
        self.local_word_freq = {}
        self.docs_words_boosts = {}

    def feed(self, doc_id, texts, get_locations):
        self.doc_count += 1
        if doc_id in self.local_word_freq:
            return

        self.local_word_freq.setdefault(doc_id, {})
        self.docs_words_boosts.setdefault(doc_id, {})

        for text, boost in texts:

            locations = get_locations(text)
            for w, l in locations.iteritems():
                global_freq = self.global_word_freq.setdefault(w, 0)
                local_freq = len(l)
                self.global_word_freq[w] = global_freq + local_freq

                old_local_freq = self.local_word_freq[doc_id].setdefault(w, 0)
                self.local_word_freq[doc_id][w] = old_local_freq + local_freq

                boost = max(self.docs_words_boosts[doc_id].get(w, 0), boost)

                if boost != 1:  # save some space..
                    self.docs_words_boosts[doc_id][w] = boost

    def f(self, term, doc_id):
        return self.local_word_freq[doc_id][term]

    # Algorithm adapted from wikipedia.
    # tf(t, d) = 0.5 + \frac{0.5 f(t, d)}{max(f(w, d), w \in d)}
    def tf(self, term, doc_id):
        o = self.f(term, doc_id) / max(self.local_word_freq[doc_id].values())
        return 0.5 + (0.5 * o)

    # Wikipedia is amazing
    # idf(t, D) = \log \frac{|D|}{|{d \in D : t \in D}|}
    def idf(self, term):
        appearance = 0  # Avoid division by 0 problem
        for doc_id, words in self.local_word_freq.iteritems():
            appearance += 1 if term in words else 0
        # Add a 1 so we are approximately the same.. not really
        return math.log(self.doc_count / appearance, 2)

    def tfidf(self, term, doc_id):
        boost = self.docs_words_boosts[doc_id].get(term, 1)
        return self.tf(term, doc_id) * self.idf(term) * boost

    def tfidf_doc(self, doc_id):
        doc = self.local_word_freq[doc_id]
        scores = []
        for word in doc:
            scores.append((word, round(self.tfidf(word, doc_id), 2)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def offline_index(self):
        index = {}
        for doc_id in self.local_word_freq:
            scores = self.tfidf_doc(doc_id)
            for word, score in scores:
                l = index.setdefault(word, [])
                l.append((doc_id, score))
        return index
