'use strict';

module('BrowserDetect');

test('Fennec 7', function() {
    var ua = 'Mozilla/5.0 (Android; Linux armv7l; rv:7.0.1) Gecko/ Firefox/7.0.1 Fennec/7.0.1';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'm');
    equals(BrowserDetect.searchVersion(ua), 7);
});

test('Fennec 10', function() {
    var ua = 'Mozilla/5.0 (Android; Mobile; rv:10.0.4) Gecko/10.0.4 Firefox/10.0.4 Fennec/10.0.4';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'm');
    equals(BrowserDetect.searchVersion(ua), 10);
});

test('Fennec 14', function() {
    var ua = 'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'm');
    equals(BrowserDetect.searchVersion(ua), 14);
});

test('Firefox 4', function() {
    var ua = 'Mozilla/5.0 (X11; Linux i686; rv:2.0) Gecko/20100101 Firefox/4.0';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'fx');
    equals(BrowserDetect.searchVersion(ua), 4);
});

test('Firefox 12', function() {
    var ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0';

    equals(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua), 'fx');
    equals(BrowserDetect.searchVersion(ua), 12);
});

test('Windows versions', function() {
    var ua;

    ua = 'Mozilla/5.0 (Windows NT 5.0; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'winxp');
    ua = 'Mozilla/5.0 (Windows NT 5.01; WOW64; rv:12.0) Gecko/20100101 Firefox/13.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'winxp');
    ua = 'Mozilla/5.0 (Windows NT 5.1; WOW64; rv:12.0) Gecko/20100101 Firefox/14.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'winxp');
    ua = 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:12.0) Gecko/20100101 Firefox/15.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win7');
    ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/16.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win7');
    ua = 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:12.0) Gecko/20100101 Firefox/17.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win8');
    ua = 'Mozilla/5.0 (Windows NT 4.0; WOW64; rv:12.0) Gecko/20100101 Firefox/4.0';
    equals(BrowserDetect.searchString(BrowserDetect.dataOS, ua), 'win');
});

});
