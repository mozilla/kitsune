import React from 'react';
import {default as mochaJsdom, rerequire} from 'mocha-jsdom';
import {expect} from 'chai';
import sinon from 'sinon';

import mochaGettext from './fixtures/mochaGettext.js';
import mochaK from './fixtures/mochaK.js';
import mochaJquery from './fixtures/mochaJquery.js';
import mochaUnderscore from './fixtures/mochaUnderscore.js';

describe('k', () => {
  let form;

  mochaJsdom({useEach: true, url: 'http://localhost'});
  mochaJquery();
  mochaK();
  mochaUnderscore();
  /* globals window, $, k */

  describe('TagsFilter', () => {
    beforeEach(() => {
      rerequire('../tags.filter.js');

      let sandbox = (
        <div>
          <section className="tag-filter">
            <form method="get" action="">
              <input type="text"
                     name="tagged"
                     className="text tags-autocomplete"
                     defaultValue="Go"
                     data-vocabulary={JSON.stringify({
                       'Name 1': 'slug-1',
                       'Name 2': 'slug-2',
                       'Name 3': 'slug-3',
                     })}/>
              <input type="submit" defaultValue="Go" />
            </form>
          </section>
        </div>
      );
      React.render(sandbox, window.document.body);

      k.TagsFilter.init($('body'));
      // Don't let forms submit
      $('form').submit((e) => e.preventDefault());
    });

    function check(input, output) {
      $('form').find('input[type="text"]').val(input);
      $('form').submit();
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
