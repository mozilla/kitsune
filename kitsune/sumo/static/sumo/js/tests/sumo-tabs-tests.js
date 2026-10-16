import { expect } from "chai";

import tabsInit from "sumo/js/sumo-tabs";

describe("sumo-tabs", () => {
  const MORE_BUTTON_WIDTH = 50;
  let originalOffsetWidth;

  before(() => {
    // jsdom doesn't do layout, so read each width from a data-width attribute.
    originalOffsetWidth = Object.getOwnPropertyDescriptor(
      window.HTMLElement.prototype,
      "offsetWidth"
    );
    Object.defineProperty(window.HTMLElement.prototype, "offsetWidth", {
      configurable: true,
      get() {
        if (this.classList.contains("tabs--button")) {
          return MORE_BUTTON_WIDTH;
        }
        return Number(this.dataset.width || 0);
      },
    });
  });

  after(() => {
    Object.defineProperty(window.HTMLElement.prototype, "offsetWidth", originalOffsetWidth);
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  // Four 100px tabs, by default in a 300px row where, with the 50px "More" button, only two fit.
  function renderTabs(selectedIndex, rowWidth = 300) {
    const items = ["One", "Two", "Three", "Four"]
      .map(
        (label, i) => `
        <li class="tabs--item" data-width="100">
          <a class="tabs--link${i === selectedIndex ? " is-active" : ""}" href="#">
            <span>${label}</span>
          </a>
        </li>`
      )
      .join("");
    document.body.innerHTML = `
      <nav class="tabs"><ul class="tabs--list" data-width="${rowWidth}">${items}</ul></nav>`;
    tabsInit();
  }

  function shownInRow() {
    return [...document.querySelectorAll(".tabs--list > .tabs--item:not(.is-hidden)")].map(
      (li) => li.textContent.trim()
    );
  }

  function shownInMore() {
    return [...document.querySelectorAll(".tabs--dropdown > li:not(.is-hidden)")].map((li) =>
      li.textContent.trim()
    );
  }

  it("keeps the first tabs that fit when nothing is selected", () => {
    renderTabs(null);
    expect(shownInRow()).to.deep.equal(["One", "Two"]);
    expect(shownInMore()).to.deep.equal(["Three", "Four"]);
  });

  it("never moves the selected tab into More", () => {
    renderTabs(3);
    expect(shownInRow()).to.deep.equal(["One", "Four"]);
    expect(shownInMore()).to.deep.equal(["Two", "Three"]);
  });

  it("leaves the row alone when the selected tab already fits", () => {
    renderTabs(0);
    expect(shownInRow()).to.deep.equal(["One", "Two"]);
    expect(shownInMore()).to.deep.equal(["Three", "Four"]);
  });

  it("shows every tab and no More when the tabs fit without it", () => {
    // 400px of tabs fit in 420px, but not with room for the 50px "More" button too.
    renderTabs(null, 420);
    expect(shownInRow()).to.deep.equal(["One", "Two", "Three", "Four"]);
    expect(document.querySelector(".tabs--item-more").classList.contains("is-hidden")).to.equal(
      true
    );
  });
});
