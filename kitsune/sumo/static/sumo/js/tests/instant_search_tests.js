import {default as mochaJsdom, rerequire} from 'mocha-jsdom';
import {default as chai, expect} from 'chai';
import React from 'react';
import chaiLint from 'chai-lint';
import sinon from 'sinon';

import mochaK from './fixtures/mochaK.js';
import mochaJquery from './fixtures/mochaJquery.js';
import mochaGoogleAnalytics from './fixtures/mochaGoogleAnalytics.js';
import mochaNunjucks from './fixtures/mochaNunjucks.js';
import mochaGettext from './fixtures/mochaGettext.js';

chai.use(chaiLint);

describe('instant search', () => {
  mochaJsdom({useEach: true, url: 'http://localhost'});
  mochaJquery();
  mochaK();
  mochaGoogleAnalytics();
  mochaGettext();
  mochaNunjucks();
  /* globals window, document, $ */

  describe('', () => {
    let $sandbox;
    let clock;

    beforeEach(() => {
      clock = sinon.useFakeTimers();
      window.matchMedia = () => {
        return {
          matches: false,
          addListener: () => {}
        }
      }

      global.matchMedia = window.matchMedia;
      window.Mzp = {};
      window._localStorage = { getItem: () => undefined };

      rerequire('../i18n.js');
      global.interpolate = global.window.interpolate;
      rerequire('../search_utils.js');
      rerequire('../instant_search.js');

      let content = (
        <div>
          <div id="main-content"/>
          <form data-instant-search="form" action="" method="get" className="simple-search-form">
            <input type="search" name="q" className="searchbox" id="search-q"/>
            <button type="submit" title="{{ _('Search') }}" className="submit-button">Search</button>
          </form>
        </div>
      );
      React.render(content, document.body);
    });

    afterEach(() => {
      React.unmountComponentAtNode(document.body);
      clock.restore();
    });

    it('shows and hides the main content correctly', () => {
      const $searchInput = $('#search-q');
      expect($('#main-content').css('display')).to.not.equal('none');

      $searchInput.val('test');
      $searchInput.keyup();
      expect($('#main-content').css('display')).to.equal('none');

      $searchInput.val('');
      $searchInput.keyup();
      expect($('#main-content').css('display')).to.not.equal('none');
    });

    it('shows the search query at the top of the page', () => {
      const query = 'search query';
      const requestExpectation = cxhrMock.expects('request')
        .once()
        .withArgs(sinon.match.string, sinon.match(opts => opts.data.q === query));

      const $searchInput = $('#search-q');
      $searchInput.val(query);
      $searchInput.keyup();

      clock.tick(200);
      // call the callback to actually render things
      requestExpectation.firstCall.args[1].success({
        num_results: 0,
        q: query,
      });

      const $searchResultHeader = $('.search-results-heading');
      expect($searchResultHeader.find('span').first().text()).to.equal(query);
    });

    it('escapes the search query at the top of the page', () => {
      const query = '<';
      const requestExpectation = cxhrMock.expects('request');

      const $searchInput = $('#search-q');
      $searchInput.val(query);
      $searchInput.keyup();

      clock.tick(200);
      // call the callback to actually render things
      requestExpectation.firstCall.args[1].success({
        num_results: 0,
        q: query,
      });

      const queryElem = document.querySelectorAll('.search-results-heading span')[0];
      expect(queryElem.innerHTML).to.equal('&lt;');
    });
  });
});
