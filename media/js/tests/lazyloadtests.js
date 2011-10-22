$(document).ready(function(){

"use strict";

var lazyLoadFixture = {
    setup: function() {

    },
    teardown: function() {

    }
};

module('lazyload', lazyLoadFixture);

asyncTest('load original image', function() {
    var img = new Image();
    $(img).addClass("lazy");
    $(img).attr("original-src", "test.jpg");
    $.fn.lazyload.loadOriginalImage($(img));
    equals($(img).attr("src"), 'test.jpg', 'src attribute set correctly');
    equals($(img).attr("original-src"), undefined, 'original-src attribute cleared correctly');
    start();
});
});
