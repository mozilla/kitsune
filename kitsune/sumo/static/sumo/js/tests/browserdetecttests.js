import {expect} from 'chai';
import {default as mochaJsdom, rerequire} from 'mocha-jsdom';

import mochaUnderscore from './fixtures/mochaUnderscore.js';

describe('BrowserDetect', () => {
  mochaJsdom({useEach: true, url: 'http://localhost'});
  mochaUnderscore();
  /* globals window */

  let BrowserDetect;

  beforeEach(() => {
    rerequire('../browserdetect.js');

    BrowserDetect = window.BrowserDetect;
  });

  describe('Fennec versions', () => {
    it('should detect Fennec 7', () => {
      let ua = 'Mozilla/5.0 (Android; Linux armv7l; rv:7.0.1) Gecko/ Firefox/7.0.1 Fennec/7.0.1';
      expect(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua)).to.equal('m');
      expect(BrowserDetect.searchVersion(ua)).to.equal(7);
      expect(BrowserDetect.detect(ua)).to.deep.equal(['m', 7, 'android']);
    });

    it('should detect Fennec 10', () => {
      let ua = 'Mozilla/5.0 (Android; Mobile; rv:10.0.4) Gecko/10.0.4 Firefox/10.0.4 Fennec/10.0.4';
      expect(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua)).to.equal('m');
      expect(BrowserDetect.searchVersion(ua)).to.equal(10);
      expect(BrowserDetect.detect(ua)).to.deep.equal(['m', 10, 'android']);
    });

    it('should detect Fennec 14', () => {
      let ua = 'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0';
      expect(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua)).to.equal('m');
      expect(BrowserDetect.searchVersion(ua)).to.equal(14);
      expect(BrowserDetect.detect(ua)).to.deep.equal(['m', 14, 'android']);
    });
  });

  describe('Firefox versions', () => {
    it('should detect Firefox 4', () => {
      let ua = 'Mozilla/5.0 (X11; Linux i686; rv:2.0) Gecko/20100101 Firefox/4.0';
      expect(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua)).to.equal('fx');
      expect(BrowserDetect.searchVersion(ua)).to.equal(4);
      expect(BrowserDetect.detect(ua)).to.deep.equal(['fx', 4, 'linux']);
    });

    it('should detect Firefox 12', () => function() {
      let ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0';
      expect(BrowserDetect.searchString(BrowserDetect.dataBrowser, ua)).to.equal('fx');
      expect(BrowserDetect.searchVersion(ua)).to.equal(12);
      expect(BrowserDetect.detect(ua)).to.deep.equal(['fx', 12, 'win7']);
    });
  });

  describe('Windows versions', () => {
    let cases = [
      {
        ua: 'Mozilla/5.0 (Windows NT 5.0; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0',
        expected: ['fx', 12, 'winxp'],
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 5.01; WOW64; rv:12.0) Gecko/20100101 Firefox/13.0',
        expected: ['fx', 13, 'winxp'],
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 5.1; WOW64; rv:12.0) Gecko/20100101 Firefox/14.0',
        expected: ['fx', 14, 'winxp'],
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:12.0) Gecko/20100101 Firefox/15.0',
        expected: ['fx', 15, 'win7'],
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/16.0',
        expected: ['fx', 16, 'win7'],
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:12.0) Gecko/20100101 Firefox/17.0',
        expected: ['fx', 17, 'win8'],
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 4.0; WOW64; rv:12.0) Gecko/20100101 Firefox/4.0',
        expected: ['fx', 4, 'win'],
      },
    ];

    for (let case_ of cases) {
      it(`should detect ${case_.expected}`, () => {
        expect(BrowserDetect.searchString(BrowserDetect.dataOS, case_.ua)).to.equal(case_.expected[2]);
        expect(BrowserDetect.detect(case_.ua)).to.deep.equal(case_.expected);
      });
    }
  });

  describe('Firefox OS', function() {
    let cases = [
      {
        ua: 'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0',
        expected: ['fxos', 1, 'fxos'],
      },
      {
        ua: 'Mozilla/5.0 (Mobile; nnnn; rv:18.1) Gecko/18.1 Firefox/18.1',
        expected: ['fxos', 1.1, 'fxos'],
      },
      {
        ua: 'Mozilla/5.0 (Mobile; nnnn; rv:26.0) Gecko/26.0 Firefox/26.0',
        expected: ['fxos', 1.2, 'fxos'],
      },
      {
        ua: 'Mozilla/5.0 (Mobile; nnnn; rv:28.0) Gecko/28.0 Firefox/28.0',
        expected: ['fxos', 1.3, 'fxos'],
      },
    ];

    for (let case_ of cases) {
      it(`should detect ${case_.expected}`, () => {
        expect(BrowserDetect.detect(case_.ua)).to.deep.equal(case_.expected);
      });
    }
  });

  describe('Firefox for iOS', () => {
    it('all platforms', () => {
      let uas = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4',
        'Mozilla/5.0 (iPad; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4',
        'Mozilla/5.0 (iPod touch; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 Mobile/12H143 Safari/600.1.4'
      ];
      for (let ua of uas) {
        expect(BrowserDetect.detect(ua)).to.deep.equal(['fxios', 1.0, 'ios']);
      }
    });

    let cases = [
      {
        ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0.0 Mobile/12D508 Safari/600.1.4',
        version: 1.0,
      },
      {
        ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0.1 Mobile/12D508 Safari/600.1.4',
        version: 1.0,
      },
      {
        ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.1.0 Mobile/12D508 Safari/600.1.4',
        version: 1.1,
      },
    ];

    for (let case_ of cases) {
      it(`version ${case_.version}`, () => {
        expect(BrowserDetect.detect(case_.ua)[1]).to.equal(case_.version);
      });
    }
  });
});
