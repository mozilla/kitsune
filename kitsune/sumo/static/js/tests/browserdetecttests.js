'use strict';

module('BrowserDetect');

test('Fennec 7', function() {
    var ua = 'Mozilla/5.0 (Android; Linux armv7l; rv:7.0.1) Gecko/ Firefox/7.0.1 Fennec/7.0.1';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'm');
    equals(BrowserDetect.searchVersion(ua), 7);

    deepEqual(BrowserDetect.detect(ua), ['m', 7, 'android']);
});

test('Fennec 10', function() {
    var ua = 'Mozilla/5.0 (Android; Mobile; rv:10.0.4) Gecko/10.0.4 Firefox/10.0.4 Fennec/10.0.4';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'm');
    equals(BrowserDetect.searchVersion(ua), 10);

    deepEqual(BrowserDetect.detect(ua), ['m', 10, 'android']);
});

test('Fennec 14', function() {
    var ua = 'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'm');
    equals(BrowserDetect.searchVersion(ua), 14);

    deepEqual(BrowserDetect.detect(ua), ['m', 14, 'android']);
});

test('Firefox 4', function() {
    var ua = 'Mozilla/5.0 (X11; Linux i686; rv:2.0) Gecko/20100101 Firefox/4.0';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'fx');
    equals(BrowserDetect.searchVersion(ua), 4);

    deepEqual(BrowserDetect.detect(ua), ['fx', 4, 'linux']);
});

test('Firefox 12', function() {
    var ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'fx');
    equals(BrowserDetect.searchVersion(ua), 12);

    deepEqual(BrowserDetect.detect(ua), ['fx', 12, 'win7']);
});

test('Windows versions', function() {
    var ua;

    ua = 'Mozilla/5.0 (Windows NT 5.0; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'winxp');
    deepEqual(BrowserDetect.detect(ua), ['fx', 12, 'winxp']);
    ua = 'Mozilla/5.0 (Windows NT 5.01; WOW64; rv:12.0) Gecko/20100101 Firefox/13.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'winxp');
    deepEqual(BrowserDetect.detect(ua), ['fx', 13, 'winxp']);
    ua = 'Mozilla/5.0 (Windows NT 5.1; WOW64; rv:12.0) Gecko/20100101 Firefox/14.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'winxp');
    deepEqual(BrowserDetect.detect(ua), ['fx', 14, 'winxp']);
    ua = 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:12.0) Gecko/20100101 Firefox/15.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win7');
    deepEqual(BrowserDetect.detect(ua), ['fx', 15, 'win7']);
    ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/16.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win7');
    deepEqual(BrowserDetect.detect(ua), ['fx', 16, 'win7']);
    ua = 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:12.0) Gecko/20100101 Firefox/17.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win8');
    deepEqual(BrowserDetect.detect(ua), ['fx', 17, 'win8']);
    ua = 'Mozilla/5.0 (Windows NT 4.0; WOW64; rv:12.0) Gecko/20100101 Firefox/4.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win');
    deepEqual(BrowserDetect.detect(ua), ['fx', 4, 'win']);
});

test('Firefox OS', function() {
    var ua;

    ua = 'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0';
    deepEqual(BrowserDetect.detect(ua), ['fxos', 1, 'fxos']);
    ua = 'Mozilla/5.0 (Mobile; nnnn; rv:18.1) Gecko/18.1 Firefox/18.1';
    deepEqual(BrowserDetect.detect(ua), ['fxos', 1.1, 'fxos']);
    ua = 'Mozilla/5.0 (Mobile; nnnn; rv:26.0) Gecko/26.0 Firefox/26.0';
    deepEqual(BrowserDetect.detect(ua), ['fxos', 1.2, 'fxos']);
    ua = 'Mozilla/5.0 (Mobile; nnnn; rv:28.0) Gecko/28.0 Firefox/28.0';
    deepEqual(BrowserDetect.detect(ua), ['fxos', 1.3, 'fxos']);
});
