/* globals ShowFor:false, module:false, tests:false, test:false, equals:false,
   deepEqual:false, assert:false, console:false, ok:false */
(function() {

/* Tests for showfor */
'use strict';

/*
 * Returns an object with the same prototype and properties as a ShowFor
 * object, but for which the ShowFor constructor is not called. It will
 * be bound to the passed $sandbox.
*/
function showForNoInit($sandbox) {
  var sf = Object.create(ShowFor.prototype);
  sf.$container = $sandbox;
  sf.state = {};
  return sf;
}


module('ShowFor', {
  setup: function() {
    this.$sandbox = tests.createSandbox('#showfor');
    this.showFor = showForNoInit(this.$sandbox);
  },
  teardown: function() {
    this.$sandbox.remove();
  },
});

test('loadData', function() {
  this.showFor.loadData();

  // Assert that data was loaded
  equals(typeof this.showFor.data, 'object');
  equals(this.showFor.data.products.length, 3);
  equals(this.showFor.data.versions.firefox.length, 5);

  function unorderedEquals(arr1, arr2) {
    console.log('unorderedEquals', arr1, arr2);
    equals(arr1.length, arr2.length);
    arr1.forEach(function(o) {
      ok(arr2.indexOf(o) > -1);
    });
  }

  // Assert that the denormalized forms were pulled out
  unorderedEquals(this.showFor.productSlugs, ['firefox', 'mobile', 'firefox-os']);
  unorderedEquals(this.showFor.platformSlugs, ['web', 'android', 'linux', 'mac', 'winxp', 'win7', 'win8']);
  equals(this.showFor.versionSlugs.fx24, 'firefox');
  equals(this.showFor.versionSlugs['fxos1.2'], 'firefox-os');
  equals(this.showFor.versionSlugs.m24, 'mobile');
});

test('updateUI', function() {
  var _orig = {
    browser: BrowserDetect.browser,
    version: BrowserDetect.version,
    OS: BrowserDetect.OS,
  };

  this.showFor.loadData();

  var $versionFx = this.$sandbox.find('.product[data-product=firefox] select.version');
  var $platformFx = this.$sandbox.find('.product[data-product=firefox] select.platform');
  var $versionM = this.$sandbox.find('.product[data-product=mobile] select.version');

  BrowserDetect.browser = 'fx';
  BrowserDetect.version = 26.0;
  BrowserDetect.OS = 'winxp';
  sessionStorage.removeItem('showfor::persist');
  this.showFor.updateUI();
  equals($versionFx.val(), 'version:fx26');
  equals($platformFx.val(), 'platform:winxp');

  BrowserDetect.browser = 'm';
  BrowserDetect.version = 23.0;
  BrowserDetect.OS = 'android';
  sessionStorage.removeItem('showfor::persist');
  this.showFor.updateUI();
  equals($versionM.val(), 'version:m23');

  // cleanup
  BrowserDetect.browser = _orig.browser;
  BrowserDetect.version = _orig.version;
  BrowserDetect.OS = _orig.OS;
});

test('updateState', function() {
  this.showFor.updateState();

  equals(this.showFor.state.firefox.enabled, true);
  equals(this.showFor.state.firefox.platform, 'win8');
  equals(this.showFor.state.firefox.version.min, 24);
  equals(this.showFor.state.firefox.version.max, 25);
  equals(this.showFor.state.firefox.version.slug, 'fx24');

  equals(this.showFor.state.mobile.enabled, true);
  equals(this.showFor.state.mobile.version.min, 24);
  equals(this.showFor.state.mobile.version.max, 25);
  equals(this.showFor.state.mobile.version.slug, 'm24');

  equals(this.showFor.state.persona.enabled, true);

  // now change some things
  this.$sandbox.find('[value="product:persona"]').prop('checked', false);
  this.$sandbox.find('[data-product="mobile"] select.version').val('version:m26');
  this.$sandbox.find('[data-product="firefox"] select.platform').val('platform:linux');

  // and check again
  this.showFor.updateState();

  equals(this.showFor.state.firefox.enabled, true);
  equals(this.showFor.state.firefox.platform, 'linux');
  equals(this.showFor.state.firefox.version.min, 24);
  equals(this.showFor.state.firefox.version.max, 25);
  equals(this.showFor.state.firefox.version.slug, 'fx24');

  equals(this.showFor.state.mobile.enabled, true);
  equals(this.showFor.state.mobile.version.min, 26);
  equals(this.showFor.state.mobile.version.max, 27);
  equals(this.showFor.state.mobile.version.slug, 'm26');

  equals(this.showFor.state.persona.enabled, false);

});

test('initShowFuncs', function() {
  // Replace the matchesCriteria function with a spy of sorts.
  this.showFor.matchesCriteria = function(criteria) {
    return criteria;
  };

  this.showFor.initShowFuncs();

  // Now each showfor element should have a function stored in
  // .data('show-func')that returns the criteria that was calcuated by
  // initShowFuncs.
  var $elems = this.$sandbox.find('.for');
  deepEqual($elems.eq(0).data('show-func')(), ['fx24']);
  deepEqual($elems.eq(1).data('show-func')(), ['fx24', 'win']);
  deepEqual($elems.eq(2).data('show-func')(), ['=fxos1.1']);
  deepEqual($elems.eq(3).data('show-func')(), ['not m25']);
});

test('showAndHide', function() {
  var $elems = this.$sandbox.find('.for');

  var yes = function() { return true; };
  var no = function() { return false; };

  $elems.eq(0).data('show-func', yes);
  $elems.eq(1).data('show-func', no);
  $elems.eq(2).data('show-func', no);
  // The last element (#3) doesn't have a show func.

  this.showFor.showAndHide();
  
  // 0's show-func returns true. it should be visible
  ok($elems.eq(0).is(':visible'));
  // 1 and 2's show-funcs returns false. they should be hidden.
  ok(!$elems.eq(1).is(':visible'));
  ok(!$elems.eq(2).is(':visible'));
  // 3 doesn't have a show func. It should be visible.
  ok($elems.eq(3).is(':visible'));
});

test('matchesCriteria', function() {
  this.showFor.loadData();

  var check = function(criteria, expected) {
    var msg = 'Expected ' + JSON.stringify(criteria) + ' to return ' + expected;
    equals(this.showFor.matchesCriteria(criteria), expected, msg);
  }.bind(this);

  this.showFor.state = {
    firefox: {
      enabled: true,
      platform: 'win8',
      version: {min: 24, max: 25, slug: 'fx24'}
    }
  };

  // One selector criteria
  check(['fx23'], true);
  check(['fx24'], true);
  check(['fx25'], false);
  check(['=fx23'], false);
  check(['=fx24'], true);
  check(['=fx25'], false);
  // Version and platform
  check(['fx23', 'win8'], true);
  check(['fx24', 'win8'], true);
  check(['fx24', 'win'], true);
  check(['fx24', 'linux'], false);
  check(['fx25', 'win8'], false);
  check(['fx25', 'win'], false);
  check(['fx25', 'linux'], false);
  // not tests single
  check(['not fx23'], false);
  check(['not fx24'], false);
  check(['not fx25'], true);
  check(['not =fx23'], true);
  check(['not =fx24'], false);
  check(['not =fx25'], true);
  // not test multiple
  check(['not fx23', 'win'], false);
  check(['not fx24', 'win'], false);
  check(['not fx25', 'win'], true);

  check(['not fx23', 'linux'], false);
  check(['not fx24', 'linux'], false);
  check(['not fx25', 'linux'], false);

  check(['not fx23', 'not win'], false);
  check(['not fx24', 'not win'], false);
  check(['not fx25', 'not win'], false);

  check(['not fx23', 'not linux'], false);
  check(['not fx24', 'not linux'], false);
  check(['not fx25', 'not linux'], true);

  // What about mixed products?
  this.showFor.state = {
    firefox: {
      enabled: true,
      platform: 'win8',
      version: {min: 24, max: 25, slug: 'fx24'}
    },
    mobile: {
      enabled: true,
      version: {min: 24, max: 25, slug: 'm24'}
    },
  };

  // This is basically an OR.
  check(['fx23', 'm23'], true);
  check(['fx23', 'm24'], true);
  check(['fx23', 'm25'], true);
  check(['fx24', 'm23'], true);
  check(['fx24', 'm24'], true);
  check(['fx24', 'm25'], true);
  check(['fx25', 'm23'], true);
  check(['fx25', 'm24'], true);
  check(['fx25', 'm25'], false);

  // What about disabled stuff?
  this.showFor.state = {
    firefox: {
      enabled: true,
    },
    mobile: {
      enabled: false,
    },
  };

  check(['fx'], true);
  check(['m'], false);
  check(['fx', 'm'], true);

  check(['not fx'], false);
  check(['not m'], true);
  check(['not fx', 'm'], false);
  check(['fx', 'not m'], true);
  check(['not fx', 'not m'], true);
});

})();
