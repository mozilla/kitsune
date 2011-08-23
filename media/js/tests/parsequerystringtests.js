/*
 * Tests for k.getQueryParamsAsDict()
 */

$(document).ready(function(){

// Object.keys() shim
if (!Object.keys) {
    Object.keys = function keys(object) {
        var keys = [];
        for (var name in object) {
            if (object.hasOwnProperty(name)) {
                keys.push(name);
            }
        }
        return keys;
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
    equals('woot', params['test']);
});

test('two params', function() {
    var url = 'http://example.com/?x=foo&y=bar',
        params = k.getQueryParamsAsDict(url);
    equals(Object.keys(params).length, 2);
    equals('foo', params['x']);
    equals('bar', params['y']);
});

test('google url', function() {
    var url = 'http://www.google.com/url?sa=t&source=web&cd=1&sqi=2&ved=0CDEQFjAA&url=http%3A%2F%2Fsupport.mozilla.com%2F&rct=j&q=firefox%20help&ei=OsBSTpbZBIGtgQfgzv3yBg&usg=AFQjCNFIV7wgd9Pnr0m3Ofc7r1zVTNK8dw',
        params = k.getQueryParamsAsDict(url);
    equals(Object.keys(params).length, 10);
    equals('firefox help', params['q']);
});

});
