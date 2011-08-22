/*
 * Tests for k.getQueryParamsAsDict()
 */

$(document).ready(function(){

module('k.getQueryParamsAsDict');

test('no params', function() {
    var queryString = '',
        params = k.getQueryParamsAsDict(queryString);
    equals(0, Object.keys(params).length);
});

test('two params', function() {
    var queryString = 'http://example.com/?x=foo&y=bar',
        params = k.getQueryParamsAsDict(queryString);
    equals(2, Object.keys(params).length);
    equals('foo', params['x']);
    equals('bar', params['y']);
});

test('google url', function() {
    var queryString = 'http://www.google.com/url?sa=t&source=web&cd=1&sqi=2&ved=0CDEQFjAA&url=http%3A%2F%2Fsupport.mozilla.com%2F&rct=j&q=firefox%20help&ei=OsBSTpbZBIGtgQfgzv3yBg&usg=AFQjCNFIV7wgd9Pnr0m3Ofc7r1zVTNK8dw',
        params = k.getQueryParamsAsDict(queryString);
    equals(10, Object.keys(params).length);
    equals('firefox help', params['q']);
});

});
