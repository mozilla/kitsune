import { expect } from "chai";
import sinon from "sinon";

import { addGAEventListeners } from "sumo/js/analytics";

describe("analytics", () => {
  describe("addGAEventListeners", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="container">
          <a href="/kb/private-article" data-event-name="link_click">Private article</a>
        </div>`;
      window.gtag = sinon.fake();
    });

    afterEach(() => {
      document.body.innerHTML = "";
      delete window.gtag;
      delete document.body.dataset.privateSearch;
    });

    [
      { privateSearch: false, events: 1 },
      { privateSearch: true, events: 0 },
    ].forEach(({ privateSearch, events }) => {
      it(`sends ${events} link_click events when private search is ${privateSearch}`, () => {
        if (privateSearch) {
          document.body.dataset.privateSearch = "true";
        }
        addGAEventListeners("#container");
        const link = document.querySelector("#container a");
        // jsdom doesn't implement navigation.
        link.addEventListener("click", (event) => event.preventDefault());

        link.click();

        const sent = window.gtag.getCalls().filter((call) => call.args[1] === "link_click");
        expect(sent).to.have.length(events);
        if (events) {
          expect(sent[0].args[2].link_url).to.equal("/kb/private-article");
        }
      });
    });
  });
});
