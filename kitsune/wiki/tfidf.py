from __future__ import division

import math
import re
from operator import itemgetter
from heapq import nlargest
from itertools import repeat, ifilter

# Counter class from http://code.activestate.com/recipes/576611-counter-class/
# we are running on py2.6, so..
class Counter(dict):
    '''Dict subclass for counting hashable objects.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    >>> Counter('zyzygy')
    Counter({'y': 3, 'z': 2, 'g': 1})

    '''

    def __init__(self, iterable=None, **kwds):
        '''Create a new, empty Counter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = Counter()                           # a new, empty counter
        >>> c = Counter('gallahad')                 # a new counter from an iterable
        >>> c = Counter({'a': 4, 'b': 2})           # a new counter from a mapping
        >>> c = Counter(a=4, b=2)                   # a new counter from keyword args

        '''
        self.update(iterable, **kwds)

    def __missing__(self, key):
        return 0

    def most_common(self, n=None):
        '''List the n most common elements and their counts from the most
        common to the least.  If n is None, then list all element counts.

        >>> Counter('abracadabra').most_common(3)
        [('a', 5), ('r', 2), ('b', 2)]

        '''
        if n is None:
            return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
        return nlargest(n, self.iteritems(), key=itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each as many times as its count.

        >>> c = Counter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        If an element's count has been set to zero or is a negative number,
        elements() will ignore it.

        '''
        for elem, count in self.iteritems():
            for _ in repeat(None, count):
                yield elem

    # Override dict methods where the meaning changes for Counter objects.

    @classmethod
    def fromkeys(cls, iterable, v=None):
        raise NotImplementedError(
            'Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

    def update(self, iterable=None, **kwds):
        '''Like dict.update() but add counts instead of replacing them.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = Counter('which')
        >>> c.update('witch')           # add elements from another iterable
        >>> d = Counter('watch')
        >>> c.update(d)                 # add elements from another counter
        >>> c['h']                      # four 'h' in which, witch, and watch
        4

        '''
        if iterable is not None:
            if hasattr(iterable, 'iteritems'):
                if self:
                    self_get = self.get
                    for elem, count in iterable.iteritems():
                        self[elem] = self_get(elem, 0) + count
                else:
                    dict.update(self, iterable) # fast path when counter is empty
            else:
                self_get = self.get
                for elem in iterable:
                    self[elem] = self_get(elem, 0) + 1
        if kwds:
            self.update(kwds)

    def copy(self):
        'Like dict.copy() but returns a Counter instance instead of a dict.'
        return Counter(self)

    def __delitem__(self, elem):
        'Like dict.__delitem__() but does not raise KeyError for missing values.'
        if elem in self:
            dict.__delitem__(self, elem)

    def __repr__(self):
        if not self:
            return '%s()' % self.__class__.__name__
        items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
        return '%s({%s})' % (self.__class__.__name__, items)

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       and at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative and zero counts, add-in an empty counter:
    #       c += Counter()

    def __add__(self, other):
        '''Add counts from two counters.

        >>> Counter('abbb') + Counter('bcc')
        Counter({'b': 4, 'c': 2, 'a': 1})


        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] + other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __sub__(self, other):
        ''' Subtract count, but keep only results with positive counts.

        >>> Counter('abbbc') - Counter('bccd')
        Counter({'b': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] - other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __or__(self, other):
        '''Union is the maximum of value in either of the input counters.

        >>> Counter('abbb') | Counter('bcc')
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _max = max
        result = Counter()
        for elem in set(self) | set(other):
            newcount = _max(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result

    def __and__(self, other):
        ''' Intersection is the minimum of corresponding counts.

        >>> Counter('abbb') & Counter('bcc')
        Counter({'b': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _min = min
        result = Counter()
        if len(self) < len(other):
            self, other = other, self
        for elem in ifilter(self.__contains__, other):
            newcount = _min(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result

def find_word_locations_en_like(s):
    """Builds an index in the format of {word: location}. This method also
    strips out any stop words. This is a english like search. For Chinese-like
    (no spaces and what not), use establish_word_locations_zh_like
    """
    s = s.lower()
    words = ['']
    for c in s:
        if c == ' ':
            words.append('')
        elif c == '.': # We want to treat . as a big stop. Add two space.
            words.append('')
            words.append('')
        elif c in ',;:': # We want to treat , as a single gap
            words.append('')
        elif c in '\'"[]1234567890/\\?!()\t-_\n':
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
            scores.append((word, self.tfidf(word, doc_id)))
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
