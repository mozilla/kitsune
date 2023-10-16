import {default as chai, expect} from 'chai';
import chaiLint from 'chai-lint';
import sinon from 'sinon';
import sinonChai from 'sinon-chai';

import {
  getQueryParamsAsDict,
  getReferrer,
  getSearchQuery,
  unquote,
  safeString,
  safeInterpolate,
} from "sumo/js/main";

chai.use(chaiLint);
chai.use(sinonChai);

describe('k', () => {
  describe('getQueryParamsAsDict', () => {
    it('should return an empty object for no params', () => {
      let url = 'http://example.com';
      let params = getQueryParamsAsDict(url);
      expect(params).to.deep.equal({});
    });

    it('should parse a query string with one parameter', () => {
      let url = 'http://example.com/?test=woot';
      let params = getQueryParamsAsDict(url);
      expect(params).to.deep.equal({test: 'woot'});
    });

    it('should parse a query string with two paramaters', () => {
      let url = 'http://example.com/?x=foo&y=bar';
      let params = getQueryParamsAsDict(url);
      expect(params).to.deep.equal({x: 'foo', y: 'bar'});
    });

    it('should parse this Google url', () => {
      var url = ('http://www.google.com/url?sa=t&source=web&cd=1&sqi=2&' +
                 'ved=0CDEQFjAA&url=http%3A%2F%2Fsupport.mozilla.com%2F&' +
                 'rct=j&q=firefox%20help&ei=OsBSTpbZBIGtgQfgzv3yBg&' +
                 'usg=AFQjCNFIV7wgd9Pnr0m3Ofc7r1zVTNK8dw');
      let params = getQueryParamsAsDict(url);
      expect(params).to.deep.equal({
        sa: 't',
        source: 'web',
        cd: '1',
        sqi: '2',
        ved: '0CDEQFjAA',
        url: 'http://support.mozilla.com/',
        rct: 'j',
        q: 'firefox help',
        ei: 'OsBSTpbZBIGtgQfgzv3yBg',
        usg: 'AFQjCNFIV7wgd9Pnr0m3Ofc7r1zVTNK8dw',
      });
    });
  });

  describe('getReferrer', () => {
    it('should recognize search referrers', () => {
      let params = {as: 's', s: 'cookies'};
      let actual = getReferrer(params);
      expect(actual).to.equal('search');
    });

    it('should recognize inproduct referrers', () => {
      let params = {as: 'u'};
      let actual = getReferrer(params);
      expect(actual).to.equal('inproduct');
    });

    it('should fall back to `document.referrer`', () => {
      let referrer = 'http://google.com/?q=cookies';
      expect(document.referrer).to.equal(referrer);
      expect(getReferrer({})).to.equal(referrer);
    });
  });

  describe('getSearchQuery', () => {
    it('should return the s query string for local search referrers', () => {
      let params = {as: 's', s: 'cookies'};
      let referrer = 'search';
      expect(getSearchQuery(params, referrer)).to.equal('cookies');
    });

    it('should return an empty string fro inproduct referrers', () => {
      let params = {as: 'u', s: 'wrong'};
      let referrer = 'inproduct';
      expect(getSearchQuery(params, referrer)).to.equal('');
    });

    it('should detect external search parameters from google', () => {
      let referrer = 'http://google.com/?q=cookies';
      expect(getSearchQuery({}, referrer)).to.equal('cookies');
    });
  });

  describe('unquote', () => {
    it('should return undefined for undefined input', () => {
      expect(unquote(undefined)).to.beUndefined();
    });

    it('should unquote simply quoted strings', () => {
      expect(unquote('"delete cookies"')).to.equal('delete cookies');
    });

    it('should handle escaped quotes', () => {
      expect(unquote('"\\"delete\\" cookies"')).to.equal('"delete" cookies');
    });

    it('should handle escaped quotes with no other quotes', () => {
      expect(unquote('\\"delete\\" cookies')).to.equal('"delete" cookies');
    });

    it('should pass strings without quotes through unmodified', () => {
      let s = 'cookies';
      expect(unquote(s)).to.equal(s);
    });
  });

  describe('safeString', () => {
    it('should escape html', function() {
      let unsafeString = '<a href="foo&\'">';
      let expectedString = '&lt;a href=&quot;foo&amp;&#39;&quot;&gt;';
      expect(safeString(unsafeString)).to.equal(expectedString);
    });
  });

  describe('safeInterpolate', () => {
    /* safeInterpolate works by delegating to `interpolate`, a Django
     * gettext function. These tests mock out interpolate and make sure
     * it was called appropriately.
     */
    let interpolateSpy;
    let oldInterpolate = global.interpolate;

    beforeEach(() => {
      interpolateSpy = global.interpolate = sinon.spy();
    });

    // We have to put interpolate back when we're done.
    after(() => {
      global.interpolate = oldInterpolate;
    });

    it('should interpolate positional user input', function() {
      let html = '<div>%s</div> %s';
      let unsafe = ['<a>', '<script>'];
      let safe = ['&lt;a&gt;', '&lt;script&gt;'];

      safeInterpolate(html, unsafe, false);

      expect(interpolateSpy).to.have.callCount(1);
      expect(interpolateSpy).to.have.been.calledWithExactly(html, safe, false);
    });

    it('should interpolate named user input', function() {
      var html = '<div>%(display)s <span>(%(name)s)</span></div>';
      let unsafe = {
        display: "<script>alert('xss');</script>",
        name: 'Jo&mdash;hn',
      };
      let safe = {
        display: '&lt;script&gt;alert(&#39;xss&#39;);&lt;/script&gt;',
        name: 'Jo&amp;mdash;hn',
      };
      safeInterpolate(html, unsafe, true);

      expect(interpolateSpy).to.have.callCount(1);
      expect(interpolateSpy).to.have.been.calledWithExactly(html, safe, true);
    });
  });
});
