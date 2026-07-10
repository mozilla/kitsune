import {expect} from 'chai';

import KBox from "sumo/js/kbox.js";

// Returns the currently-open kbox container, or null if none is open.
function openContainer() {
  return document.querySelector('.kbox-container.kbox-open');
}

describe('kbox', () => {
  describe('declarative', () => {
    let kbox;

    beforeEach(() => {
      document.body.innerHTML = `
        <div id="sandbox">
          <div class="kbox"
               data-title="ignored title"
               title="test kbox"
               data-target="#sandbox a.kbox-target"
               data-modal="true">
            <p>lorem ipsum dolor sit amet.</p>
          </div>
          <a href="#" class="kbox-target">click me</a>
        </div>`;

      kbox = new KBox(document.querySelector('.kbox'));
    });

    afterEach(() => {
      document.body.innerHTML = '';
    });

    it('should open when the target is clicked', () => {
      document.querySelector('.kbox-target').click();
      expect(openContainer()).to.not.equal(null);
    });

    it('should open programmatically', () => {
      kbox.open();
      expect(openContainer()).to.not.equal(null);
    });

    it('should close programmatically', () => {
      kbox.open();
      kbox.close();
      expect(openContainer()).to.equal(null);
    });

    it('should have the right title', () => {
      kbox.open();
      expect(document.querySelector('.kbox-title').textContent).to.equal('test kbox');
    });

    it('should have a modal overlay', () => {
      expect(document.getElementById('kbox-overlay')).to.equal(null);
      kbox.open();
      expect(document.getElementById('kbox-overlay')).to.not.equal(null);
    });

    it('destroy should clean up the container', () => {
      kbox.open();
      expect(document.querySelector('.kbox-container')).to.not.equal(null);
      kbox.destroy();
      expect(document.querySelector('.kbox-container')).to.equal(null);
    });

    it('does not throw when the element is absent', () => {
      expect(function () {
        new KBox(document.querySelector('.does-not-exist'));
      }).to.not.throw();
    });
  });
});
