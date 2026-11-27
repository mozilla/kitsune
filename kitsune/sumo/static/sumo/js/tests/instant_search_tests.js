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
      delete window.gtag;
      delete document.body.dataset.privateSearch;
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

    it('restores the main content and preserves the query when the latest search fails', () => {
      const searchInput = document.getElementById('search-q');
      const mainContent = document.getElementById('main-content');

      searchInput.value = 'test';
      fireInput(searchInput);
      clock.tick(600);
      cxhrMock.firstCall.args[1].error(new Error('request failed'));

      expect(mainContent.style.display).to.not.equal('none');
      expect(searchInput.value).to.equal('test');
    });

    it('does not recover the content when an earlier request for the same query fails', () => {
      const searchInput = document.getElementById('search-q');
      const mainContent = document.getElementById('main-content');

      searchInput.value = 'repeated query';
      fireInput(searchInput);
      clock.tick(600);

      searchInput.value = 'intermediate query';
      fireInput(searchInput);
      clock.tick(600);

      searchInput.value = 'repeated query';
      fireInput(searchInput);
      clock.tick(600);
      cxhrMock.firstCall.args[1].error(new Error('request failed'));

      expect(mainContent.style.display).to.equal('none');
      expect(searchInput.value).to.equal('repeated query');
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
      cxhrMock.firstCall.args[1].success({
        num_results: 23,
        total_is_approximate: true,
        q: 'firefox',
        product_titles: 'All Products',
        products: [],
        w: 3,
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
      });

      expect(document.querySelector('.search-results-heading').textContent)
        .to.include('Showing the most relevant results');
      expect(document.querySelector('.search-results-heading').textContent)
        .to.include('about 23 potential matches');
      expect(document.querySelector('.topic-article--text strong').textContent).to.equal('Matched');
      expect(document.querySelectorAll('.pagination a')).to.have.length(2);

      const event = JSON.parse(
        document.querySelector('.topic-article a.title').dataset.eventParameters
      );
      expect(event.search_result_source).to.equal('kb');
      expect(event.search_result_rank).to.equal(11);
      expect(event).not.to.have.property('score');
    });

    [
      { fallback_results: null, offersFeatured: false },
      {
        fallback_results: [
          { url: '/kb/featured', document_title: 'Featured article', document_summary: 'Summary' },
        ],
        offersFeatured: true,
      },
    ].forEach(({ fallback_results, offersFeatured }) => {
      it(`${offersFeatured ? 'offers' : 'does not offer'} featured articles on zero results`, () => {
        const searchInput = document.getElementById('search-q');
        const query = `nothing matches ${offersFeatured}`;
        searchInput.value = query;
        fireInput(searchInput);
        clock.tick(600);

        cxhrMock.firstCall.args[1].success({
          num_results: 0,
          q: query,
          product_titles: 'All Products',
          products: [],
          w: 3,
          results: [],
          fallback_results,
        });

        const content = document.getElementById('instant-search-content');
        expect(content.textContent.includes('featured articles')).to.equal(offersFeatured);
        expect(content.querySelectorAll('.sumo-card-grid .card')).to.have.length(
          offersFeatured ? 1 : 0
        );
      });
    });

    [
      { privateSearch: false, events: 1 },
      { privateSearch: true, events: 0 },
    ].forEach(({ privateSearch, events }) => {
      it(`sends ${events} search and result click events when private search is ${privateSearch}`, () => {
        window.gtag = sinon.fake();
        if (privateSearch) {
          document.body.dataset.privateSearch = 'true';
        }
        const searchInput = document.getElementById('search-q');
        const query = `private search ${privateSearch}`;

        // A query unlike the previous one, which the module would skip.
        searchInput.value = query;
        fireInput(searchInput);
        clock.tick(600);
        cxhrMock.firstCall.args[1].success({
          num_results: 1,
          q: query,
          product_titles: 'All Products',
          products: [],
          w: 3,
          results: [{ type: 'document', url: '/kb/private-article', title: 'Private article' }],
        });
        // jsdom doesn't implement navigation.
        document.addEventListener('click', (event) => event.preventDefault(), { once: true });
        document.querySelector('.topic-article a.title').click();

        const sent = (name) => window.gtag.getCalls().filter((call) => call.args[1] === name);
        expect(sent('search')).to.have.length(events);
        expect(sent('link_click')).to.have.length(events);
      });
    });

    [
      { name: 'kb', value: 'northwind', link: 'data-instant-search-set-params="kb=agents"', expected: 'agents' },
      { name: 'kb', value: 'northwind', link: 'data-instant-search-unset-params="kb&page"', expected: undefined },
      {
        name: 'product',
        value: 'firefox',
        link: 'data-instant-search-unset-params="product&page" data-instant-search-set-params="all_products=1"',
        expected: undefined,
      },
    ].forEach(({ name, value, link, expected }) => {
      it(`keeps the ${name} filter ${expected} chosen from the results when typing again`, () => {
        document.querySelector('form').insertAdjacentHTML(
          'beforeend',
          `<input type="hidden" name="${name}" value="${value}">`
        );
        document.body.insertAdjacentHTML(
          'beforeend',
          `<a href="#" id="kb-link" data-instant-search="link" ${link}>KB</a>`
        );
        const searchInput = document.getElementById('search-q');

        searchInput.value = 'scoped query';
        fireInput(searchInput);
        clock.tick(600);
        document.getElementById('kb-link').click();
        searchInput.value = 'scoped query again';
        fireInput(searchInput);
        clock.tick(600);

        expect(cxhrMock.firstCall.args[1].data[name]).to.equal(value);
        expect(cxhrMock.lastCall.args[1].data[name]).to.equal(expected);
      });
    });
  });
});

describe('instant search on a KB article page', () => {
  let clock;
  let cxhrMock;
  let originalMatchMedia;

  function loadArticlePage(sidebarItems) {
    document.body.className = 'document';
    document.body.innerHTML = `
      <div>
        <div id="main-content">
          <aside id="aside">
            <nav id="doc-tools">
              <ul class="sidebar-nav sidebar-folding">
                <li id="editing-tools-sidebar">
                  <span class="details-heading"></span>
                  <ul class="sidebar-nav--list">${sidebarItems}</ul>
                </li>
              </ul>
            </nav>
          </aside>
        </div>
        <form data-instant-search="form" action="" method="get" class="simple-search-form">
          <input type="search" name="q" class="searchbox" id="search-q">
        </form>
      </div>`;
  }

  function searchFor(query) {
    const searchInput = document.getElementById('search-q');
    searchInput.value = query;
    fireInput(searchInput);
    clock.tick(600);
    cxhrMock.firstCall.args[1].success({
      num_results: 0,
      q: query,
      products: [{ slug: 'firefox', title: 'Firefox' }],
    });
  }

  function filterHeadingText() {
    return document.querySelector('#instant-search-content .details-heading button').textContent.trim();
  }

  beforeEach(() => {
    clock = sinon.useFakeTimers();
    cxhrMock = sinon.fake();
    sinon.replace(CachedXHR.prototype, "request", cxhrMock);
    originalMatchMedia = global.matchMedia;
    global.matchMedia = () => ({ matches: true, addListener() {} });
  });

  afterEach(() => {
    clock.restore();
    sinon.restore();
    global.matchMedia = originalMatchMedia;
    document.body.className = '';
    document.body.innerHTML = '';
  });

  it('labels the product filter heading with the selected product', () => {
    loadArticlePage('<li><a href="/kb/article">Article</a></li>');
    searchFor('reader view');

    expect(filterHeadingText()).to.equal('All Products');
  });

  it('labels the product filter heading while hiding the empty article sidebar', () => {
    loadArticlePage('');
    searchFor('private browsing');

    expect(document.getElementById('aside').hidden).to.equal(true);
    expect(filterHeadingText()).to.equal('All Products');
  });
});
