$(document).ready(function(){

"use strict";

var tagsFilterFixture = {
    setup: function() {
        this.sandbox = tests.createSandbox('#tagsfilter');
        this.sandbox.find('section.tag-filter').attr('id', 'tag-filter');
        k.TagsFilter.init(this.sandbox);
        // Don't let the form to actually submit
        this.sandbox.find('form').submit(function(e) { e.preventDefault(); });
    },
    teardown: function() {
        this.sandbox.remove();
    }
};

module('tags.filter', tagsFilterFixture);

test('1 tags', function() {
    checkResult(this.sandbox, 'Name 2', 'slug-2');
});

test('2 tags', function() {
    checkResult(this.sandbox, 'Name 1, Name 3', 'slug-1,slug-3');
});

test('3 tags', function() {
    checkResult(this.sandbox, 'Name 1,Name 2,Name 3', 'slug-1,slug-2,slug-3');
});

test('case insensitive', function() {
    checkResult(this.sandbox, 'nAmE 1', 'slug-1');
});

test('existing filter', function() {
    var $h = $('<input type="hidden" class="current-tagged" value="slug-7">');
    this.sandbox.find('form').append($h);
    checkResult(this.sandbox, 'Name 1', 'slug-7,slug-1');
});

function checkResult($sandbox, input, expected) {
    var $form = $sandbox.find('form');
    $form.find('input[type="text"]').val(input);
    $form.submit();
    equals($form.find('input[name="tagged"]').val(), expected);
}

});