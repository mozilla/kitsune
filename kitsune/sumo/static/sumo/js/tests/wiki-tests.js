import { expect } from "chai";
import sinon from "sinon";

import {
  initTitleAndSlugCheck,
  initTranslationDraft,
  initRevisionList,
  initReadyForL10n,
  initArticlePreview,
  initPreviewDiff,
} from "sumo/js/wiki";

function jsonResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

function failResponse(status) {
  return {
    ok: false,
    status: status,
    headers: { get: () => "application/json" },
    json: async () => {
      throw new SyntaxError("no");
    },
    text: async () => "",
  };
}

function htmlResponse(html) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "text/html" },
    json: async () => JSON.parse(html),
    text: async () => html,
  };
}

function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("wiki: initTitleAndSlugCheck (verifyUnique)", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  function setup(attrs) {
    document.body.innerHTML = `
      <form data-json-url="/kb/exists"${attrs || ""}>
        <div><input id="id_title" name="title"></div>
        <div><input id="id_slug" name="slug" value="a-slug"></div>
      </form>`;
    initTitleAndSlugCheck();
    return document.getElementById("id_slug");
  }

  it("flags a slug collision on a new document", async () => {
    sinon.stub(window, "fetch").resolves(jsonResponse({ id: 5 }));
    const slug = setup();

    slug.dispatchEvent(new window.Event("change"));
    await tick();

    expect(slug.classList.contains("error")).to.equal(true);
    expect(slug.parentNode.querySelector("ul.errorlist")).to.not.equal(null);
  });

  it("does not flag when the server returns 405 (no existing doc)", async () => {
    sinon.stub(window, "fetch").resolves(failResponse(405));
    const slug = setup();

    slug.dispatchEvent(new window.Event("change"));
    await tick();

    expect(slug.classList.contains("error")).to.equal(false);
    expect(slug.parentNode.querySelector("ul.errorlist")).to.equal(null);
  });

  it("does not flag when the only match is the document being edited", async () => {
    sinon.stub(window, "fetch").resolves(jsonResponse({ id: 5 }));
    const slug = setup(' data-document-id="5"');

    slug.dispatchEvent(new window.Event("change"));
    await tick();

    expect(slug.classList.contains("error")).to.equal(false);
  });
});

describe("wiki: initTranslationDraft", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("merges all three forms' fields by name when saving a draft", async () => {
    document.body.innerHTML = `
      <form id="both_form"><input name="a" value="1"><input name="shared" value="both"></form>
      <form id="doc_form"><input name="b" value="2"></form>
      <form id="rev_form"><input name="c" value="3"><input name="shared" value="rev"></form>
      <button class="btn-draft" data-draft-url="/draft"></button>
      <div id="draft-message"></div>`;
    const fetchStub = sinon.stub(window, "fetch").resolves(jsonResponse({}));
    initTranslationDraft();

    document.querySelector(".btn-draft").click();
    await tick();

    expect(fetchStub.calledOnce).to.equal(true);
    const [url, init] = fetchStub.firstCall.args;
    expect(url).to.equal("/draft");
    expect(init.method).to.equal("POST");
    const body = new URLSearchParams(init.body);
    // Every field from every form is present (the old $.extend-by-index merge
    // dropped fields)...
    expect(body.get("a")).to.equal("1");
    expect(body.get("b")).to.equal("2");
    expect(body.get("c")).to.equal("3");
    // ...and on a name collision the later form (rev_form) wins.
    expect(body.get("shared")).to.equal("rev");
  });

  it("wires both 'Save as Draft' buttons (top and #preview-bottom)", () => {
    // The submit button bar is rendered twice; the bottom one lives in
    // #preview-bottom and is revealed after a preview.
    document.body.innerHTML = `
      <form id="rev_form"><input name="c" value="3"></form>
      <button class="btn-draft" data-draft-url="/draft"></button>
      <div id="preview-bottom" hidden>
        <button class="btn-draft" data-draft-url="/draft"></button>
      </div>
      <div id="draft-message"></div>`;
    const fetchStub = sinon.stub(window, "fetch").returns(new Promise(function () {}));
    initTranslationDraft();

    // Click the SECOND (bottom) draft button.
    document.querySelectorAll(".btn-draft")[1].click();

    expect(fetchStub.calledOnce).to.equal(true);
    expect(fetchStub.firstCall.args[0]).to.equal("/draft");
  });
});

describe("wiki: initArticlePreview", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("wires both 'Preview Content' buttons (top and #preview-bottom)", () => {
    document.body.innerHTML = `
      <form>
        <textarea id="id_content">hello</textarea>
        <button class="btn-preview" data-preview-url="/preview"></button>
        <div id="preview"></div>
        <div id="preview-bottom" hidden>
          <button class="btn-preview" data-preview-url="/preview"></button>
        </div>
      </form>`;
    // Keep the request pending so the show-preview/lazyload path doesn't run.
    const fetchStub = sinon.stub(window, "fetch").returns(new Promise(function () {}));
    initArticlePreview();

    // Click the SECOND (bottom) preview button.
    document.querySelectorAll(".btn-preview")[1].click();

    expect(fetchStub.calledOnce).to.equal(true);
    expect(fetchStub.firstCall.args[0]).to.equal("/preview");
  });
});

describe("wiki: initPreviewDiff", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("wires both 'Preview Changes' buttons (top and #preview-bottom)", () => {
    document.body.innerHTML = `
      <div>
        <textarea id="id_content">new content</textarea>
        <button class="btn-diff"></button>
        <div id="preview-diff" hidden>
          <div class="from"></div>
          <div class="to"></div>
          <div class="output"></div>
        </div>
        <div id="preview-bottom" hidden>
          <button class="btn-diff"></button>
        </div>
      </div>`;
    initPreviewDiff();

    // Click the SECOND (bottom) diff button.
    document.querySelectorAll(".btn-diff")[1].click();

    // The handler copies the textarea into #preview-diff .to and reveals the
    // bottom button bar.
    expect(document.querySelector("#preview-diff .to").textContent).to.equal("new content");
    expect(document.getElementById("preview-bottom").hidden).to.equal(false);
  });
});

describe("wiki: initRevisionList", () => {
  let realFormData;

  beforeEach(() => {
    // wiki.js does `new FormData(form)`; Node's global (undici) FormData rejects
    // a jsdom form element, so use jsdom's implementation for these tests.
    realFormData = global.FormData;
    global.FormData = window.FormData;
  });

  afterEach(() => {
    global.FormData = realFormData;
    sinon.restore();
    sessionStorage.removeItem("revision-list-filter");
    document.body.innerHTML = "";
  });

  it("removes submit controls from the filter form", () => {
    document.body.innerHTML = `
      <div id="revision-list">
        <form class="filter" action="/revisions">
          <select name="show"><option value="all">all</option></select>
          <button type="submit">Go</button>
        </form>
      </div>`;
    initRevisionList();

    const form = document.querySelector("#revision-list form.filter");
    expect(form.querySelector('[type="submit"]')).to.equal(null);
    expect(form.querySelector("button")).to.equal(null);
  });

  it("saves filter state (excluding page) and fetches the fragment on change", async () => {
    document.body.innerHTML = `
      <div id="revision-list">
        <form class="filter" action="/revisions">
          <select name="show">
            <option value="all">all</option>
            <option value="new" selected>new</option>
          </select>
          <input type="hidden" name="page" value="3">
        </form>
      </div>
      <div id="revisions-fragment"></div>`;
    const fetchStub = sinon.stub(window, "fetch").resolves(htmlResponse("<p>rows</p>"));
    initRevisionList();

    const clock = sinon.useFakeTimers();
    document
      .querySelector('select[name="show"]')
      .dispatchEvent(new window.Event("input", { bubbles: true }));

    // Filter state is persisted synchronously, without the pagination field.
    const saved = JSON.parse(sessionStorage.getItem("revision-list-filter"));
    expect(saved).to.deep.equal({ show: "new" });

    clock.tick(250); // past the 200ms debounce
    clock.restore();
    await tick();

    expect(fetchStub.calledOnce).to.equal(true);
    const requestedUrl = fetchStub.firstCall.args[0];
    expect(requestedUrl).to.contain("show=new");
    expect(requestedUrl).to.contain("fragment=1");
    expect(document.getElementById("revisions-fragment").innerHTML).to.equal("<p>rows</p>");
  });
});

describe("wiki: initReadyForL10n", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("marks a revision ready even though the first .l10n is the column header", () => {
    // The revision list's first .l10n element is the <th> column header (no
    // link); the "mark as ready" link lives in a row's <td class="l10n">.
    document.body.innerHTML = `
      <div id="revision-list">
        <table>
          <tr><th class="l10n"><abbr>R</abbr></th></tr>
          <tr><td class="l10n">
            <a class="markasready" id="rev-5-l10n-no"
               data-url="/mark-ready/5" data-revdate="2020-01-01"></a>
          </td></tr>
        </table>
      </div>
      <div class="mzp-u-modal-content" data-modal-id="ready-for-l10n-modal">
        <input type="hidden" name="csrfmiddlewaretoken" value="tok">
        <span class="revtime"></span>
        <button id="submit-l10n" type="submit">Submit</button>
      </div>`;
    // The submit handler's success path calls Protocol Modal.closeModal(), which
    // throws without a real open modal - keep fetch pending so it never runs.
    const fetchStub = sinon.stub(window, "fetch").returns(new Promise(function () {}));
    initReadyForL10n();

    // Clicking the "X" must record the target URL (it previously wasn't, because
    // the handler was bound to the header cell, which has no link)...
    document.getElementById("rev-5-l10n-no").click();
    expect(document.querySelector("span.revtime").innerHTML).to.equal("(2020-01-01)");

    // ...so clicking Submit POSTs to it.
    document.getElementById("submit-l10n").click();
    expect(fetchStub.calledOnce).to.equal(true);
    const [url, init] = fetchStub.firstCall.args;
    expect(url).to.equal("/mark-ready/5");
    expect(init.method).to.equal("POST");
  });
});
