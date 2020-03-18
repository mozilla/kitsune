import {default as mochaJsdom, rerequire} from 'mocha-jsdom';
import {expect} from 'chai';
import React from 'react';

import mochaK from './fixtures/mochaK.js';
import mochaJquery from './fixtures/mochaJquery.js';
import mochaGettext from './fixtures/mochaGettext.js';
import mochaMarky from './fixtures/mochaMarky.js';

describe('k', () => {
  mochaJsdom({useEach: true, url: 'http://localhost'});
  mochaJquery();
  mochaK();
  mochaGettext();
  mochaMarky();
  /* globals window, document, $, k */

  describe('linkCrashIds', () => {

    beforeEach(() => {
      rerequire('../questions.js');
    });

    afterEach(() => {
      React.unmountComponentAtNode(document.body);
    });

    it('should link one crash ID', () => {
      let sandbox = (
        <section>
          <h1>Firefox keeps crashing</h1>
          <p>Firefox keeps crashing</p>
          <p>
            This is my crash ID:<br/>
            bp-6ec83338-f37e-4ee1-aef4-0e66c2120808
          </p>
          <div className="stem"></div>
        </section>
      );
      React.render(sandbox, document.body);

      k.linkCrashIds($('body'));
      expect($('.crash-report').length).to.equal(1);
    });

    it('should link multiple crash IDs', function() {
      let sandbox = (
        <section>
          <h1>Firefox keeps crashing</h1>
          <p>Firefox keeps crashing</p>
          <p>
            Here's a list of my crash IDs (copied directly from about:crashes):<br/>
            bp-6ec83338-f37e-4ee1-aef4-0e66c212080808.08.1217:52
            bp-d8951614-c928-44ed-902c-6ccb6212080808.08.1217:52
            bp-5eb7d4ec-5f9e-4cbf-9335-a574c212071717.07.1211:29
            bp-15a73687-dabf-4014-9c03-b97b3212071717.07.1211:27
            bp-f894adf7-9ff8-4f21-8564-da425212071111.07.1218:22
          </p>
          <div className="stem"></div>
        </section>
      );
      React.render(sandbox, document.body);

      k.linkCrashIds($('body'));
      expect($('.crash-report').length).to.equal(5);
    });

    it("shouldn't link invalid crash IDs", function() {
      let sandbox = (
        <section>
          <p>The following will look like an invalid crash ID that hasn't been processed yet:</p>
          <p>765879E6-CFE7-43A7-BE93-B2F322E67649</p>
        </section>
      );
      React.render(sandbox, document.body);
      k.linkCrashIds($('body'));

      expect($('.crash-report').length).to.equal(0);
    });

    it("shouldn't link crash IDs without 'bp-'", function() {
      let sandbox = (
        <section>
          <p>Now, crash IDs without 'bp-' at the beginning shouldn't get linked either</p>
          <p>6ec83338-f37e-4ee1-aef4-0e66c2120808</p>
        </section>
      );
      React.render(sandbox, document.body);

      k.linkCrashIds($('body'));
      expect($('.crash-report').length).to.equal(0);
    });
  });
});
