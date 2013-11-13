(function() {

/*
 * Tests for common utility functions (k.*).
 */

'use strict';

// Object.keys() shim
if (!Object.keys) {
    Object.keys = function keys(object) {
        var ks = [];
        for (var name in object) {
            if (object.hasOwnProperty(name)) {
                ks.push(name);
            }
        }
        return ks;
    };
}

module('k.getQueryParamsAsDict');

test('no params', function() {
    var url = 'http://example.com/',
        params = k.getQueryParamsAsDict(url);
    equals(Object.keys(params).length, 0);
});

test('one param', function() {
    var url = 'http://example.com/?test=woot',
        params = k.getQueryParamsAsDict(url);
    equals(Object.keys(params).length, 1);
    equals('woot', params.test);
});

test('two params', function() {
    var url = 'http://example.com/?x=foo&y=bar',
        params = k.getQueryParamsAsDict(url);
    equals(Object.keys(params).length, 2);
    equals('foo', params.x);
    equals('bar', params.y);
});

test('google url', function() {
    var url = 'http://www.google.com/url?sa=t&source=web&cd=1&sqi=2&ved=0CDEQFjAA&url=http%3A%2F%2Fsupport.mozilla.com%2F&rct=j&q=firefox%20help&ei=OsBSTpbZBIGtgQfgzv3yBg&usg=AFQjCNFIV7wgd9Pnr0m3Ofc7r1zVTNK8dw',
        params = k.getQueryParamsAsDict(url);
    equals(Object.keys(params).length, 10);
    equals('firefox help', params.q);
});


module('k.getReferrer');

test('search', function() {
    // If url has `?as=s`, getReferrer should return 'search'.
    var params = {'as': 's', 's': 'cookies'};
    equals(k.getReferrer(params), 'search');
});

test('inproduct', function() {
    // If url has `?as=u`, getReferrer should return 'inproduct'.
    var params = {'as': 'u'};
    equals(k.getReferrer(params), 'inproduct');
});

test('search', function() {
    // Otherwise, getReferrer should return `document.referrer` value.
    var params = {};
    equals(k.getReferrer(params), document.referrer);
});


module('k.getSearchQuery');

test('local search referrer', function() {
    // Local search referrer should return the `s` query string param value.
    var params = {'as': 's', 's': 'cookies'},
        referrer = 'search';
    equals(k.getSearchQuery(params, referrer), 'cookies');
});

test('inproduct referrer', function() {
    // inproduct referrers should return empty string for search query.
    var params = {'as': 'u'},
        referrer = 'inproduct';
    equals(k.getSearchQuery(params, referrer), '');
});

test('external search engine (google) referrer', function() {
    // External search referrer should return the `q` query string param value
    // from the referrer url.
    var params = {},
        referrer = 'http://google.com/?q=cookies';
    equals(k.getSearchQuery(params, referrer), 'cookies');
});


module('k.unquote');

test('null param', function() {
   var undefinedString;
   equals(k.unquote(undefinedString), undefinedString);
});

test('quoted string', function() {
   var s = '"delete cookies"';
   equals(k.unquote(s), 'delete cookies');
});

test('nested quotes', function() {
   var s = '"\\"delete\\" cookies"';
   equals(k.unquote(s), '"delete" cookies');
});

test('inner quotes only', function() {
   var s = '\\"delete\\" cookies';
   equals(k.unquote(s), '"delete" cookies');
});

test('no quotes', function() {
   var s = 'cookies';
   equals(k.unquote(s), s);
});

module('k.safeString');

test('escape html', function() {
    var unsafeString = '<a href="foo&\'">',
        safeString = '&lt;a href=&quot;foo&amp;&#39;&quot;&gt;';
    equals(k.safeString(unsafeString), safeString);
});

module('k.safeInterpolate');

test('interpolate positional user input', function() {
    var html = '<div>%s</div> %s',
        unsafe = ['<a>', '<script>'],
        safe = '<div>&lt;a&gt;</div> &lt;script&gt;';
    equals(k.safeInterpolate(html, unsafe, false), safe);
});

test('interpolate named user input', function() {
    var html = '<div>%(display)s <span>(%(name)s)</span></div>',
        unsafe = {'display': "<script>alert('xss');</script>",
                  'name': 'Jo&mdash;hn'},
        safe = '<div>&lt;script&gt;alert(&#39;xss&#39;);&lt;/script&gt; <span>(Jo&amp;mdash;hn)</span></div>';
    equals(k.safeInterpolate(html, unsafe, true), safe);
});

})();
