import {default as chai, expect} from 'chai';
import React from 'react';
import chaiLint from 'chai-lint';
import sinon from 'sinon';

import "sumo/js/instant_search";
import CachedXHR from "sumo/js/cached_xhr";

chai.use(chaiLint);

describe('instant search', () => {
  describe('', () => {
    let clock;
    let cxhrMock;

    beforeEach(() => {
      clock = sinon.useFakeTimers();
      cxhrMock = sinon.fake();
      sinon.replace(CachedXHR.prototype, "request", cxhrMock);
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
      sinon.restore();
    });

    it('shows and hides the main content correctly', () => {
      const $searchInput = $('#search-q');
      expect($('#main-content').css('display')).to.not.equal('none');

      $searchInput.val('test');
      $searchInput.trigger('keyup');
      expect($('#main-content').css('display')).to.equal('none');

      $searchInput.val('');
      $searchInput.trigger('keyup');
      expect($('#main-content').css('display')).to.not.equal('none');
    });

    it('shows the search query at the top of the page', () => {
      const query = 'search query';

      const $searchInput = $('#search-q');
      $searchInput.val(query);
      $searchInput.trigger('keyup');

      clock.tick(200);
      // call the callback to actually render things
      cxhrMock.firstCall.args[1].success({
        num_results: 0,
        q: query,
      });

      const $searchResultHeader = $('.search-results-heading');
      expect($searchResultHeader.find('span').first().text()).to.equal(query);
    });

    it('escapes the search query at the top of the page', () => {
      const query = '<';

      const $searchInput = $('#search-q');
      $searchInput.val(query);
      $searchInput.trigger('keyup');

      clock.tick(200);
      // call the callback to actually render things
      cxhrMock.firstCall.args[1].success({
        num_results: 0,
        q: query,
      });

      const queryElem = document.querySelectorAll('.search-results-heading span')[0];
      expect(queryElem.innerHTML).to.equal('&lt;');
    });
  });
});
