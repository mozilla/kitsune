'use strict';

module('lazyload');

test('load original image', function() {
    var img = new Image();
    $(img).addClass('lazy');
    $(img).data('original-src', 'http://example.com/test.jpg');
    $.fn.lazyload.loadOriginalImage($(img));
    equals($(img).attr('src'), 'http://example.com/test.jpg', 'src attribute set correctly');
    equals($(img).data('original-src'), undefined, 'original-src data attribute cleared correctly');
});
