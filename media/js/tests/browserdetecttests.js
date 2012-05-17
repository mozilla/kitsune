$(document).ready(function(){

"use strict";

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

});
