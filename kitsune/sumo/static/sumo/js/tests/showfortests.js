import React from 'react';
import {default as mochaJsdom, rerequire} from 'mocha-jsdom';
import {default as chai, expect} from 'chai';
import chaiLint from 'chai-lint';
import sinon from 'sinon';

import mochaJquery from './fixtures/mochaJquery.js';
import mochaBrowserDetect from './fixtures/mochaBrowserDetect.js';

chai.use(chaiLint);

/*
* Returns an object with the same prototype and properties as a ShowFor
* object, but for which the ShowFor constructor is not called. It will
* be bound to the passed $sandbox.
*/
function showForNoInit($sandbox) {
  let sf = Object.create(window.ShowFor.prototype);
  sf.$container = $sandbox;
  sf.state = {};
  return sf;
}

function unorderedEquals(arr1, arr2) {
  let arr1Sorted = arr1.sort();
  let arr2Sorted = arr2.sort();
  expect(arr1Sorted).to.deep.equal(arr2Sorted);
}


describe('ShowFor', () => {
  mochaJsdom({useEach: true, url: 'http://localhost'});
  mochaJquery();
  /* globals window, document, $ */
  let showFor;

  beforeEach(() => {
    rerequire('../showfor.js');

    // Wow. That's a lot of data. Can we make this smaller?
    let sandbox = (
      <div>
        <span className="for" data-for="fx24"></span>
        <span className="for" data-for="fx24,win"></span>
        <span className="for" data-for="=fx25"></span>
        <span className="for" data-for="not m25"></span>

        <div className="product" data-product="firefox">
          <h2>
            <input type="checkbox" defaultChecked value="product:firefox"/>
            Firefox
          </h2>
          <div className="selectbox-wrapper">
            <select className="version" value="version:fx24">
              <option value="version:fx26" data-min="26.0" data-max="27.0">Version 26</option>
              <option value="version:fx25" data-min="25.0" data-max="26.0">Version 25</option>
              <option value="version:fx24" data-min="24.0" data-max="25.0">Version 24</option>
              <option value="version:fx23" data-min="23.0" data-max="24.0">Version 23</option>
              <option value="version:fx17" data-min="17.0" data-max="18.0">Version 17 (ESR)</option>
            </select>
          </div>
          <div className="selectbox-wrapper">
            <select className="platform">
              <option value="platform:win8">Windows 8</option>
              <option value="platform:win7">Windows 7/Vista</option>
              <option value="platform:winxp">Windows XP</option>
              <option value="platform:mac">Mac</option>
              <option value="platform:linux">Linux</option>
            </select>
          </div>
        </div>

        <div className="product" data-product="mobile">
          <h2>
            <input type="checkbox" defaultChecked value="product:mobile"/>
            Firefox for Android
          </h2>
          <div className="selectbox-wrapper">
            <select className="version" value="version:m24">
              <option value="version:m26" data-min="26.0" data-max="27.0">Version 26</option>
              <option value="version:m25" data-min="25.0" data-max="26.0">Version 25</option>
              <option value="version:m24" data-min="24.0" data-max="25.0">Version 24</option>
              <option value="version:m23" data-min="23.0" data-max="24.0">Version 23</option>
            </select>
          </div>
        </div>

        <script type="application/json" className="showfor-data" dangerouslySetInnerHTML={{__html: JSON.stringify({
          platforms: {
            firefox: [
              {title: 'Linux', slug: 'linux', visible: true},
              {title: 'Mac', slug: 'mac', visible: true},
              {title: 'Windows XP', slug: 'winxp', visible: true},
              {title: 'Windows 7', slug: 'win7', visible: true},
              {title: 'Windows 8', slug: 'win8', visible: true},
              {title: 'Windows 10', slug: 'win10', visible: true},
            ],
            mobile: [{slug: 'android'}],
            'firefox-os': [{slug: 'web'}],
          },
          products: [
            {slug: 'firefox', title: 'Firefox', platforms: ['linux', 'mac', 'winxp', 'win7', 'win8']},
            {slug: 'mobile', title: 'Firefox for Android', platforms: ['android']},
            {slug: 'firefox-os', title: 'Firefox OS', platforms: ['web']},
          ],
          'versions': {
            firefox: [
              {product: 'firefox', name: 'Version 26', default: false, min_version: 26.0, max_version: 27.0, slug: 'fx26'},
              {product: 'firefox', name: 'Version 25', default: false, min_version: 25.0, max_version: 26.0, slug: 'fx25'},
              {product: 'firefox', name: 'Version 24', default: true, min_version: 24.0, max_version: 25.0, slug: 'fx24'},
              {product: 'firefox', name: 'Version 23', default: false, min_version: 23.0, max_version: 24.0, slug: 'fx23'},
              {product: 'firefox', name: 'Version 17 (ESR)', default: false, min_version: 17.0, max_version: 18.0, slug: 'fx17'},
            ],
            mobile: [
              {product: 'mobile', name: 'Version 26', default: false, min_version: 26.0, max_version: 27.0, slug: 'm26'},
              {product: 'mobile', name: 'Version 25', default: false, min_version: 25.0, max_version: 26.0, slug: 'm25'},
              {product: 'mobile', name: 'Version 24', default: true, min_version: 24.0, max_version: 25.0, slug: 'm24'},
              {product: 'mobile', name: 'Version 23', default: false, min_version: 23.0, max_version: 24.0, slug: 'm23'},
            ],
          }
        })}}/>
      </div>
    );

    React.render(sandbox, document.body);
    showFor = showForNoInit($('body'));
  });

  describe('loadData', () => {
    beforeEach(() => {
      showFor.loadData();
    });

    it('should set the data attribute', () => {
      expect(showFor.data.products).to.have.length(3);
      expect(showFor.data.versions.firefox).to.have.length(5);
    });

    it('should pull the denormalized forms out of the data', () => {
      unorderedEquals(showFor.productSlugs, ['firefox', 'mobile', 'firefox-os']);
      unorderedEquals(showFor.platformSlugs, ['web', 'android', 'linux', 'mac', 'winxp', 'win7', 'win8', 'win10']);
      expect(showFor.versionSlugs).to.have.property('m24', 'mobile');
    });
  });

  describe('updateUI', () => {
    describe('Firefox 26 on Windows XP', () => {
      mochaBrowserDetect({
        browser: 'fx',
        version: 26.0,
        OS: 'winxp',
      });

      beforeEach(() => {
        showFor.loadData();
        showFor.updateUI();
      });

      it('should populate the UI with the values from BrowserDetect', () => {
        expect($('.product[data-product=firefox] select.version').val()).to.equal('version:fx26');
        expect($('.product[data-product=firefox] select.platform').val()).to.equal('platform:winxp');
      });
    });

    describe('Firefox for Android 23', () => {
      mochaBrowserDetect({
        browser: 'm',
        version: 23.0,
        OS: 'android',
      });

      beforeEach(() => {
        showFor.loadData();
        showFor.updateUI();
      });

      it('should populate the UI with the values from BrowserDetect', () => {
        expect($('.product[data-product=mobile] select.version').val()).to.equal('version:m23');
        expect($('.product[data-product=mobile] select.platform')).to.have.length(0);
      });
    });
  });

  describe('updateState', () => {
    mochaBrowserDetect();

    beforeEach(() => {
      showFor.loadData();
      showFor.updateUI();
      showFor.updateState();
    });

    it('should have correct initial data', () => {
      expect(showFor.state).to.deep.equal({
        firefox: {
          enabled: true,
          platform: 'winxp',
          version: {
            min: 25,
            max: 26,
            slug: 'fx25',
          },
        },
        mobile: {
          enabled: true,
          version: {
            min: 24,
            max: 25,
            slug: 'm24',
          },
        },
      });
    });

    it('should update after a change', () => {
      $('[data-product="mobile"] select.version').val('version:m26');
      $('[data-product="firefox"] select.platform').val('platform:linux');

      // and expect(showFor.matchesCriteria)).to.beGain(
      showFor.updateState();

      expect(showFor.state).to.deep.equal({
        firefox: {
          enabled: true,
          platform: 'linux',
          version: {
            min: 25,
            max: 26,
            slug: 'fx25',
          },
        },
        mobile: {
          enabled: true,
          version: {
            min: 26,
            max: 27,
            slug: 'm26',
          },
        },
      });
    });
  });

  describe('initShowFuncs', () => {
    mochaBrowserDetect();

    beforeEach(() => {
      sinon.stub(showFor, 'matchesCriteria');
      showFor.loadData();
      showFor.updateUI();
      showFor.updateState();
      showFor.initShowFuncs();
    });

    afterEach(() => {
      showFor.matchesCriteria.restore();
    });

    it('should bind `show-func` functions to `.for` elements', () => {
      // Don't use an arrow function here, because jQuery.forEach passes
      // the element as `this`.
      $('.for').each(function() {
        let callFunc = $(this).data('show-func');
        expect(callFunc).to.be.instanceof(Function);
        $(this).data('show-func')();
      });
      expect(showFor.matchesCriteria.args).to.deep.equal([
        [['fx24']],
        [['fx24', 'win']],
        [['=fx25']],
        [['not m25']],
      ]);
    });
  });

  describe('showAndHide', () => {
    mochaBrowserDetect();

    beforeEach(() => {
      showFor.loadData();
      showFor.updateUI();
      showFor.updateState();
    });

    it('should show and hide elements correctly', () => {
      let $elems = $('.for');
      let yes = () => true;
      let no = () => false;

      $elems.eq(0).data('show-func', yes);
      $elems.eq(1).data('show-func', no);
      $elems.eq(2).data('show-func', no);
      // Number 3 doesn't get a show-func, so it should default to visible

      showFor.showAndHide();

      expect($elems.eq(0).css('display')).to.equal('');
      expect($elems.eq(1).css('display')).to.equal('none');
      expect($elems.eq(2).css('display')).to.equal('none');
      expect($elems.eq(3).css('display')).to.equal('');
    });
  });

  describe('matchesCriteria', () => {
    mochaBrowserDetect();

    beforeEach(() => {
      showFor.loadData();
    });

    describe('single product', () => {
      beforeEach(() => {
        showFor.state = {
          firefox: {
            enabled: true,
            platform: 'win8',
            version: {
              min: 24,
              max: 25,
              slug: 'fx24',
            },
          },
        };
      });

      it('should handle simple selectors', () => {
        expect(showFor.matchesCriteria(['fx23'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx25'])).to.beFalse();
        expect(showFor.matchesCriteria(['=fx23'])).to.beFalse();
        expect(showFor.matchesCriteria(['=fx24'])).to.beTrue();
        expect(showFor.matchesCriteria(['=fx25'])).to.beFalse();
      });

      it('should handle selectors with version and platform', () => {
        expect(showFor.matchesCriteria(['fx23', 'win8'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24', 'win8'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24', 'win'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24', 'linux'])).to.beFalse();
        expect(showFor.matchesCriteria(['fx25', 'win8'])).to.beFalse();
        expect(showFor.matchesCriteria(['fx25', 'win'])).to.beFalse();
        expect(showFor.matchesCriteria(['fx25', 'linux'])).to.beFalse();
      });

      it('should handle `not` with a single selector', () => {
        expect(showFor.matchesCriteria(['not fx23'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx24'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx25'])).to.beTrue();
        expect(showFor.matchesCriteria(['not =fx23'])).to.beTrue();
        expect(showFor.matchesCriteria(['not =fx24'])).to.beFalse();
        expect(showFor.matchesCriteria(['not =fx25'])).to.beTrue();
      });

      it('should handle `not` with multiple selectors', () => {
        expect(showFor.matchesCriteria(['not fx23', 'win'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx24', 'win'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx25', 'win'])).to.beTrue();

        expect(showFor.matchesCriteria(['not fx23', 'linux'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx24', 'linux'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx25', 'linux'])).to.beFalse();

        expect(showFor.matchesCriteria(['not fx23', 'not win'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx24', 'not win'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx25', 'not win'])).to.beFalse();

        expect(showFor.matchesCriteria(['not fx23', 'not linux'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx24', 'not linux'])).to.beFalse();
        expect(showFor.matchesCriteria(['not fx25', 'not linux'])).to.beTrue();
      });
    });

    describe('mixed products', () => {
      beforeEach(() => {
        showFor.state = {
          firefox: {
            enabled: true,
            platform: 'win8',
            version: {min: 24, max: 25, slug: 'fx24'}
          },
          mobile: {
            enabled: true,
            version: {min: 24, max: 25, slug: 'm24'}
          }
        };
      });

      it('should handle two products as an OR', () => {
        expect(showFor.matchesCriteria(['fx23', 'm23'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx23', 'm24'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx23', 'm25'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24', 'm23'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24', 'm24'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx24', 'm25'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx25', 'm23'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx25', 'm24'])).to.beTrue();
        expect(showFor.matchesCriteria(['fx25', 'm25'])).to.beFalse();
      });
    });

    describe('disabled products', () => {
      beforeEach(() => {
        showFor.state = {
          firefox: {
            enabled: true
          },
          mobile: {
            enabled: false
          }
        };
      });

      it('should handle disabled product selectors', () => {
        expect(showFor.matchesCriteria(['fx'])).to.beTrue();
        expect(showFor.matchesCriteria(['m'])).to.beFalse();
        expect(showFor.matchesCriteria(['fx', 'm'])).to.beTrue();

        expect(showFor.matchesCriteria(['not fx'])).to.beFalse();
        expect(showFor.matchesCriteria(['not m'])).to.beTrue();
        expect(showFor.matchesCriteria(['not fx', 'm'])).to.beFalse();
        expect(showFor.matchesCriteria(['fx', 'not m'])).to.beTrue();
        expect(showFor.matchesCriteria(['not fx', 'not m'])).to.beTrue();
      });
    });

    describe('windows special cases', () => {
      beforeEach(() => {
        showFor.state = {
          firefox: {
            enabled: true,
            platform: 'win8'
          }
        };
      });

      it('should recognize `win` as all version of windows', () => {
        let winTestCases = {
          'winxp': true,
          'win7': true,
          'win8': true,
          'win10': true,
          'linux': false,
          'mac': false,
        };

        for (var winVersion in winTestCases) {
          var expected = winTestCases[winVersion];
          showFor.state.firefox.platform = winVersion;
          expect(showFor.matchesCriteria(['win'])).to.equal(expected);
          expect(showFor.matchesCriteria(['not win'])).to.equal(!expected);
        }
      });
    });
  });
});
