import { expect } from "chai";
import sinon from "sinon";

import Marky, { attachTypeahead, parseDoc } from "sumo/js/markup";

// Build a textarea with a selection range.
function textareaWith(value, start, end) {
  document.body.innerHTML = '<textarea id="ta"></textarea>';
  const ta = document.getElementById("ta");
  ta.value = value;
  ta.selectionStart = start === undefined ? value.length : start;
  ta.selectionEnd = end === undefined ? value.length : end;
  return ta;
}

// Invoke a button's click handler directly with a stub event.
function click(button) {
  button.handleClick({ preventDefault() {} });
}

describe("markup (Marky)", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("wraps the selected text with the open/close tags", () => {
    const ta = textareaWith("hello world", 0, 5); // "hello" selected
    const bold = new Marky.SimpleButton("Bold", "'''", "'''", "bold text", "btn-bold").bind(ta);
    click(bold);
    expect(ta.value).to.equal("'''hello''' world");
    // The wrapped text stays selected.
    expect(ta.value.substring(ta.selectionStart, ta.selectionEnd)).to.equal("hello");
  });

  it("inserts the default text when nothing is selected", () => {
    const ta = textareaWith("", 0, 0);
    const bold = new Marky.SimpleButton("Bold", "'''", "'''", "bold text", "btn-bold").bind(ta);
    click(bold);
    expect(ta.value).to.equal("'''bold text'''");
  });

  it("applies the markup to every line for everyline buttons", () => {
    const ta = textareaWith("a\nb", 0, 3); // both lines selected
    const list = new Marky.SimpleButton("Numbered List", "# ", "", "item", "btn-ol", true).bind(ta);
    click(list);
    expect(ta.value).to.equal("# a\n# b");
  });

  it("renders a titled button node with its classes", () => {
    const ta = textareaWith("", 0, 0);
    const bold = new Marky.SimpleButton("Bold", "'''", "'''", "bold text", "btn-bold").bind(ta);
    const node = bold.node();
    expect(node.tagName).to.equal("BUTTON");
    expect(node.getAttribute("title")).to.equal("Bold");
    expect(node.classList.contains("btn-bold")).to.equal(true);
  });

  it("createCustomToolbar appends button nodes to the toolbar", () => {
    document.body.innerHTML =
      '<div class="editor-tools"></div><textarea id="id_content"></textarea>';
    Marky.createCustomToolbar(".editor-tools", "#id_content", [
      new Marky.SimpleButton("Bold", "'''", "'''", "bold text", "btn-bold"),
    ]);
    const toolbar = document.querySelector(".editor-tools");
    expect(toolbar.querySelectorAll("button.markup-toolbar-button").length).to.equal(1);
  });

  it("createCustomToolbar is a no-op when the textarea is missing", () => {
    document.body.innerHTML = '<div class="editor-tools"></div>';
    expect(function () {
      Marky.createCustomToolbar(".editor-tools", "#does-not-exist", [
        new Marky.SimpleButton("Bold", "'''", "'''", "bold text", "btn-bold"),
      ]);
    }).to.not.throw();
    expect(document.querySelector(".editor-tools").children.length).to.equal(0);
  });
});

describe("markup: parseDoc", () => {
  it("parses an HTML string into a queryable document", () => {
    const doc = parseDoc(
      '<div class="main-content"><h2 id="w_intro">Intro</h2><h2 id="w_more">More</h2></div>'
    );
    expect(doc.querySelector(".main-content")).to.not.equal(null);
    expect(doc.querySelectorAll("[id^='w_']").length).to.equal(2);
    expect(doc.querySelector("#w_intro").textContent).to.equal("Intro");
  });
});

describe("markup: attachTypeahead", () => {
  let input;

  beforeEach(() => {
    document.body.innerHTML = '<input id="ta-input">';
    input = document.getElementById("ta-input");
  });

  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  function list() {
    return document.querySelector("ul.marky-autocomplete");
  }

  // Type a term and let the 300ms debounce fire against fake timers.
  function type(value, source, onSelect) {
    attachTypeahead(input, source, onSelect || function () {});
    const clock = sinon.useFakeTimers();
    input.value = value;
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300);
    clock.restore();
  }

  function key(k) {
    input.dispatchEvent(new window.KeyboardEvent("keydown", { key: k }));
  }

  it("debounces input and queries the source with the typed term", () => {
    const source = sinon.spy();
    attachTypeahead(input, source, function () {});
    const clock = sinon.useFakeTimers();
    input.value = "fire";
    input.dispatchEvent(new window.Event("input"));
    expect(source.called).to.equal(false); // still within the debounce window
    clock.tick(300);
    expect(source.calledOnce).to.equal(true);
    expect(source.firstCall.args[0]).to.equal("fire");
    clock.restore();
  });

  it("does not query the source when the input is empty", () => {
    const source = sinon.spy();
    attachTypeahead(input, source, function () {});
    const clock = sinon.useFakeTimers();
    input.value = "";
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300);
    expect(source.called).to.equal(false);
    clock.restore();
  });

  it("renders results and selects one on mousedown", () => {
    const onSelect = sinon.spy();
    type("f", (term, cb) => cb([{ label: "Firefox" }, { label: "Focus" }]), onSelect);

    const ul = list();
    expect(ul.hidden).to.equal(false);
    expect(ul.children.length).to.equal(2);
    expect(ul.children[0].textContent).to.equal("Firefox");

    ul.children[1].dispatchEvent(new window.Event("mousedown"));
    expect(onSelect.calledOnce).to.equal(true);
    expect(onSelect.firstCall.args[0]).to.deep.equal({ label: "Focus" });
    expect(list().hidden).to.equal(true); // closes after a pick
  });

  it("navigates with arrow keys and picks the highlighted item on Enter", () => {
    const onSelect = sinon.spy();
    type("x", (term, cb) => cb([{ label: "a" }, { label: "b" }, { label: "c" }]), onSelect);

    key("ArrowDown"); // index 0
    key("ArrowDown"); // index 1
    key("ArrowUp"); // back to index 0
    key("Enter");

    expect(onSelect.calledOnce).to.equal(true);
    expect(onSelect.firstCall.args[0]).to.deep.equal({ label: "a" });
  });

  it("closes the list on Escape", () => {
    type("x", (term, cb) => cb([{ label: "a" }]));
    expect(list().hidden).to.equal(false);
    key("Escape");
    expect(list().hidden).to.equal(true);
  });

  it("ignores an out-of-order response from a superseded search", () => {
    // Capture each request's callback so we can resolve them out of order.
    const requests = [];
    attachTypeahead(input, (term, cb) => requests.push({ term, cb }), () => {});
    const clock = sinon.useFakeTimers();

    input.value = "a";
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300); // fires the "a" request

    input.value = "ab";
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300); // fires the newer "ab" request
    clock.restore();

    expect(requests.length).to.equal(2);
    // Newer response lands first...
    requests[1].cb([{ label: "ab-result" }]);
    // ...then the older (superseded) one arrives and must NOT overwrite it.
    requests[0].cb([{ label: "a-result" }]);

    const labels = Array.prototype.map.call(list().children, (li) => li.textContent);
    expect(labels).to.deep.equal(["ab-result"]);
  });
});

describe("markup: MediaButton upload link", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  function htmlResponse(htmlStr) {
    return {
      ok: true,
      status: 200,
      headers: { get: () => "text/html" },
      json: async () => JSON.parse(htmlStr),
      text: async () => htmlStr,
    };
  }

  it("opens the gallery in a new tab and closes the modal when Upload Media is clicked", () => {
    document.body.innerHTML =
      '<div class="editor" data-media-search-url="/gallery/async" data-media-gallery-url="/gallery/">' +
      '<textarea id="id_content"></textarea></div>';
    // openModal() fires an apiFetch (updateResults) on open; stub it.
    sinon.stub(window, "fetch").resolves(htmlResponse('<ol id="media-list"></ol>'));
    const openStub = sinon.stub(window, "open");

    const btn = new Marky.MediaButton();
    btn.bind(document.getElementById("id_content"));
    btn.openModal({ preventDefault() {} });

    const uploadLink = document.querySelector("a.upload");
    expect(uploadLink).to.not.equal(null);
    uploadLink.click();

    // The gallery is opened explicitly (not left to the anchor, which the modal
    // teardown would have detached before the browser could follow it).
    expect(openStub.calledOnce).to.equal(true);
    expect(openStub.firstCall.args[0]).to.contain("/gallery/");
    expect(openStub.firstCall.args[1]).to.equal("_blank");
    // And the modal was destroyed on close.
    expect(document.querySelector("a.upload")).to.equal(null);
  });
});
