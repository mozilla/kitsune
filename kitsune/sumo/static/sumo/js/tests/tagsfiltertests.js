import {expect} from 'chai';

import TagsFilter from "sumo/js/tags.filter";

describe('k', () => {
  describe('TagsFilter', () => {
    beforeEach(() => {
      $('body').empty().html(`
        <div>
          <section class="tag-filter">
            <form method="get" action="">
              <input type="text"
                     name="tagged"
                     class="text tags-autocomplete"
                     value="Go"
                     data-vocabulary="{
                       &quot;Name 1&quot;: &quot;slug-1&quot;,
                       &quot;Name 2&quot;: &quot;slug-2&quot;,
                       &quot;Name 3&quot;: &quot;slug-3&quot;
                     }">
              <input type="submit" value="Go">
            </form>
          </section>
        </div>`
      );

      TagsFilter.init($('body'));
      // Don't let forms submit
      $('form').on("submit", (e) => e.preventDefault());
    });

    function check(input, output) {
      $('form').find('input[type="text"]').val(input);
      $('form').trigger("submit");
      expect($('form').find('input[name="tagged"]').val()).to.equal(output);
    }

    it('should work with one tag', () => {
      check('Name 1', 'slug-1');
    });

    it('should work with two tags', () => {
      check('Name 1, Name 2', 'slug-1,slug-2');
    });

    it('should work with three tags', () => {
      check('Name 1, Name 2, Name 3', 'slug-1,slug-2,slug-3');
    });

    it('should be case insensitive', () => {
      check('nAmE 1', 'slug-1');
    });

    it("shouldn't overwrite pre-existing values", () => {
      let $h = $('<input type="hidden" class="current-tagged" value="slug-7">');
      $('form').append($h);
      check('Name 1', 'slug-7,slug-1');
    });
  });
});
