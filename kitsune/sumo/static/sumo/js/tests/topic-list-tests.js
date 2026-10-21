import { expect } from "chai";

import { initTopicList } from "sumo/js/topic-list";

const ROWS = [
  { title: "Zoom in on pages", updated: "2026-03-01T10:00:00+00:00" },
  { title: "alpha settings", updated: "2026-05-01T10:00:00+00:00" },
  { title: "Beta features", updated: "2026-01-01T10:00:00+00:00" },
  { title: "Undated tips", updated: "" },
];

function renderList(rows = ROWS) {
  document.body.innerHTML = `
    <div data-list-toolbar>
      <div data-list-controls class="is-hidden">
        <select data-list-sort>
          <option value="server">Most helpful</option>
          <option value="updated">Recently updated</option>
          <option value="title">A–Z</option>
        </select>
      </div>
    </div>
    <section data-topic-list>
      ${rows
        .map(
          (row) => `
        <article class="topic-doc-list--item" data-title="${row.title}" data-updated="${row.updated}"></article>`
        )
        .join("")}
    </section>`;
  initTopicList();
}

function titles() {
  return Array.from(document.querySelectorAll(".topic-doc-list--item")).map((row) => row.dataset.title);
}

function sortBy(value) {
  const select = document.querySelector("[data-list-sort]");
  select.value = value;
  select.dispatchEvent(new window.Event("change"));
}

describe("topic-list", () => {
  let originalLang;

  beforeEach(() => {
    originalLang = document.documentElement.lang;
  });

  afterEach(() => {
    document.documentElement.lang = originalLang;
    document.body.innerHTML = "";
  });

  it("reveals the controls once enhanced", () => {
    renderList();

    expect(document.querySelector("[data-list-controls]").classList.contains("is-hidden")).to.equal(false);
  });

  [
    ["server", ["Zoom in on pages", "alpha settings", "Beta features", "Undated tips"]],
    ["updated", ["alpha settings", "Zoom in on pages", "Beta features", "Undated tips"]],
    ["title", ["alpha settings", "Beta features", "Undated tips", "Zoom in on pages"]],
  ].forEach(([order, expected]) => {
    it(`sorts by ${order}`, () => {
      renderList();

      sortBy("title");
      sortBy(order);

      expect(titles()).to.deep.equal(expected);
    });
  });

  it("uses the page language's collation for A-Z", () => {
    const rows = ["Zebra", "Äpple", "Apple"].map((title) => ({ title, updated: "" }));
    document.documentElement.lang = "sv";
    renderList(rows);

    sortBy("title");

    expect(titles()).to.deep.equal(["Apple", "Zebra", "Äpple"]);
  });
});
