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
    $(img).data("original-src", "test.jpg");
    $.fn.lazyload.loadOriginalImage($(img));
    equals($(img).attr("src"), 'test.jpg', 'src attribute set correctly');
    equals($(img).data("original-src"), undefined, 'original-src data attribute cleared correctly');
    start();
});
});
