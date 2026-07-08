import { expect } from "chai";
import sinon from "sinon";

import { loadImage, loadAllImages, lazyload } from "sumo/js/utils/lazyload";

describe("utils/lazyload", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    delete window.IntersectionObserver;
  });

  describe("loadImage", () => {
    it("swaps data-original-src into src and drops the lazy class", () => {
      document.body.innerHTML =
        '<img class="lazy" data-original-src="http://example.com/test.jpg">';
      const img = document.querySelector("img");

      loadImage(img);

      expect(img.getAttribute("src")).to.equal("http://example.com/test.jpg");
      expect(img.hasAttribute("data-original-src")).to.equal(false);
      expect(img.classList.contains("lazy")).to.equal(false);
    });
  });

  describe("loadAllImages", () => {
    it("loads every lazy image under the root immediately", () => {
      document.body.innerHTML = `
        <div id="root">
          <img class="lazy" data-original-src="/a.jpg">
          <img class="lazy" data-original-src="/b.jpg">
        </div>`;
      loadAllImages(document.getElementById("root"));

      const imgs = document.querySelectorAll("#root img");
      expect(imgs[0].getAttribute("src")).to.equal("/a.jpg");
      expect(imgs[1].getAttribute("src")).to.equal("/b.jpg");
      expect(document.querySelectorAll("#root img.lazy")).to.have.length(0);
    });
  });

  describe("lazyload", () => {
    it("loads everything immediately when IntersectionObserver is unavailable", () => {
      // jsdom has no IntersectionObserver, so this is the path exercised here.
      document.body.innerHTML = `
        <div id="root">
          <img class="lazy" data-original-src="/a.jpg">
          <img class="lazy" data-original-src="/b.jpg">
        </div>`;
      lazyload(document.getElementById("root"));

      const imgs = document.querySelectorAll("#root img");
      expect(imgs[0].getAttribute("src")).to.equal("/a.jpg");
      expect(imgs[1].getAttribute("src")).to.equal("/b.jpg");
    });

    it("observes lazy images when IntersectionObserver is available", () => {
      const observe = sinon.spy();
      window.IntersectionObserver = class {
        constructor(cb) {
          this.cb = cb;
        }
        observe(el) {
          observe(el);
        }
        unobserve() {}
      };

      document.body.innerHTML =
        '<img class="lazy" data-original-src="/a.jpg"><img data-original-src="/b.jpg">';
      lazyload(document);

      // Only the img.lazy[data-original-src] is observed; not yet loaded.
      expect(observe.calledOnce).to.equal(true);
      expect(document.querySelector("img.lazy").getAttribute("src")).to.equal(
        null
      );
    });
  });
});
