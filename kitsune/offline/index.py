from __future__ import division

import math

def find_word_locations_en_like(s):
    """Builds an index in the format of {word: location}. This method also
    strips out any stop words. This is a english like search. For Chinese-like
    (no spaces and what not), use establish_word_locations_zh_like
    """
    s = s.lower()
    words = ['']
    for c in s:
        if c in ' -':
            words.append('')
        elif c == '.': # We want to treat . as a big stop. Add two space.
            words.append('')
            words.append('')
        elif c in ',;:': # We want to treat , as a single gap
            words.append('')
        elif c in '\'"[]1234567890/\\?!()\t_\n':
            continue
        elif c in 'abcdefghijklmnopqrstuvwxyz':
            words[-1] += c
        else:
            continue # something weird..

    locations = {}
    for i, w in enumerate(words):
        if w:
            l = locations.setdefault(w, [])
            l.append(i)
            locations[w] = l

    return locations

class TFIDFAnalysis(object):
    def __init__(self):
        self.doc_count = 0
        self.global_word_freq = {}
        self.local_word_freq = {}
        self.docs_words_boosts = {}
        self.done = False

    def feed(self, doc_id, texts, get_locations):
        if self.done:
            raise Exception

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

                if boost != 1: # save some space..
                    self.docs_words_boosts[doc_id][w] = boost

    def f(self, term, doc_id):
        return self.local_word_freq[doc_id][term]

    # Awesome sauce
    # http://en.wikipedia.org/wiki/Tf%E2%80%93idf

    # Algorithm adapted from wikipedia.
    # tf(t, d) = 0.5 + \frac{0.5 f(t, d)}{max(f(w, d), w \in d)}
    def tf(self, term, doc_id):
        return 0.5 + (0.5 * self.f(term, doc_id)) / (max(self.local_word_freq[doc_id].values()))

    # Wikipedia is amazing
    # idf(t, D) = \log \frac{|D|}{|{d \in D : t \in D}|}
    def idf(self, term):
        appearance = 0 # Avoid division by 0 problem
        for doc_id, words in self.local_word_freq.iteritems():
            appearance += 1 if term in words else 0
        # Add a 1 so we are approximately the same.. not really
        return math.log(self.doc_count / appearance, 2)

    def tfidf(self, term, doc_id):
        return self.tf(term, doc_id) * self.idf(term) * self.docs_words_boosts[doc_id].get(term, 1)

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
