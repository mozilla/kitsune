import {expect, use} from 'chai';
import chaiLint from 'chai-lint';
import sinon from 'sinon';

import "sumo/js/instant_search";
import CachedXHR from "sumo/js/cached_xhr";

use(chaiLint);

// The module registers its handlers with native document.addEventListener, and
// jQuery's .trigger() only invokes jQuery-registered handlers - so drive the
// module with a real bubbling DOM event instead. Construct it from window.Event
// (jsdom's class) rather than the bare global Event (Node's), so it passes
// jsdom's dispatchEvent brand-check; global.Event can't be overridden because
// chai's plugin system relies on Node's Event.
function fireInput(el) {
  el.dispatchEvent(new window.Event('input', { bubbles: true }));
}

describe('instant search', () => {
  describe('', () => {
    let clock;
    let cxhrMock;

    beforeEach(() => {
      clock = sinon.useFakeTimers();
      cxhrMock = sinon.fake();
      sinon.replace(CachedXHR.prototype, "request", cxhrMock);
      document.body.innerHTML = `
        <div>
          <div id="main-content"></div>
          <form data-instant-search="form" action="" method="get" class="simple-search-form">
            <input type="search" name="q" class="searchbox" id="search-q">
            <button type="submit" title="Search" class="submit-button">Search</button>
          </form>
        </div>`;
    });

    afterEach(() => {
      clock.restore();
      sinon.restore();
    });

    it('shows and hides the main content correctly', () => {
      const searchInput = document.getElementById('search-q');
      const mainContent = document.getElementById('main-content');
      expect(mainContent.style.display).to.not.equal('none');

      searchInput.value = 'test';
      fireInput(searchInput);
      expect(mainContent.style.display).to.equal('none');

      searchInput.value = '';
      fireInput(searchInput);
      expect(mainContent.style.display).to.not.equal('none');
    });

    it('shows the search query at the top of the page', () => {
      const query = 'search query';

      const searchInput = document.getElementById('search-q');
      searchInput.value = query;
      fireInput(searchInput);

      clock.tick(600);
      // call the callback to actually render things
      cxhrMock.firstCall.args[1].success({
        num_results: 0,
        q: query,
      });

      const queryElem = document.querySelector('.search-results-heading span');
      expect(queryElem.textContent).to.equal(query);
    });

    it('escapes the search query at the top of the page', () => {
      const query = '<';

      const searchInput = document.getElementById('search-q');
      searchInput.value = query;
      fireInput(searchInput);

      clock.tick(600);
      // call the callback to actually render things
      cxhrMock.firstCall.args[1].success({
        num_results: 0,
        q: query,
      });

      const queryElem = document.querySelectorAll('.search-results-heading span')[0];
      expect(queryElem.innerHTML).to.equal('&lt;');
    });

    it('renders approximate hybrid results with compact pagination', () => {
      const searchInput = document.getElementById('search-q');
      searchInput.value = 'firefox';
      fireInput(searchInput);

      clock.tick(600);
      const hybridResponse = {
        num_results: 23,
        total_is_approximate: true,
        q: 'firefox',
        product_titles: 'All Products',
        products: [],
        w: 3,
        search_session: 'opaque-search-session',
        results: [{
          type: 'document',
          url: '/kb/article',
          title: 'Article',
          search_summary: '<strong>Matched</strong> summary',
          rank: 11,
          evidence_locale: 'en-US',
          display_locale: 'en-US',
          locale_fallback: false,
        }],
        pagination: {
          number: 2,
          has_previous: true,
          has_next: true,
        },
      };
      cxhrMock.firstCall.args[1].success(hybridResponse);

      expect(document.querySelector('.search-results-heading').textContent)
        .to.include('About 23');
      expect(document.querySelector('.topic-article--text strong').textContent).to.equal('Matched');
      expect(document.querySelectorAll('.pagination a')).to.have.length(2);

      document.querySelector('.pagination .next a').dispatchEvent(
        new window.Event('click', {bubbles: true})
      );
      expect(cxhrMock.secondCall.args[1].data.page).to.equal('3');
      expect(cxhrMock.secondCall.args[1].data.search_session)
        .to.equal('opaque-search-session');

      cxhrMock.secondCall.args[1].success({
        ...hybridResponse,
        search_session: 'replacement-search-session',
        pagination: {
          number: 1,
          has_previous: false,
          has_next: true,
        },
      });
      expect(history.state.params).not.to.have.property('page');
      expect(history.state.params.search_session).to.equal('replacement-search-session');

      searchInput.value = 'thunderbird';
      fireInput(searchInput);
      clock.tick(600);
      expect(cxhrMock.thirdCall.args[1].data).not.to.have.property('page');
      expect(cxhrMock.thirdCall.args[1].data).not.to.have.property('search_session');

      const event = JSON.parse(
        document.querySelector('.topic-article a.title').dataset.eventParameters
      );
      expect(event.search_result_source).to.equal('kb');
      expect(event.search_result_rank).to.equal(11);
      expect(event).not.to.have.property('score');
    });
  });
});
