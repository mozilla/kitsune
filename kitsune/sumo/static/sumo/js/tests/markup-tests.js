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
    delete window.requestAnimationFrame;
    delete window.cancelAnimationFrame;
    document.body.innerHTML = "";
  });

  function list() {
    return document.querySelector("ul.marky-autocomplete");
  }

  // jsdom has no requestAnimationFrame, and repositioning is throttled through
  // it, so stand one in whose frames we can run when we want them.
  function fakeFrames() {
    let pending = [];
    window.requestAnimationFrame = (cb) => pending.push(cb);
    window.cancelAnimationFrame = () => {
      pending = [];
    };
    return function runFrames() {
      const frames = pending;
      pending = [];
      frames.forEach((cb) => cb());
    };
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

  it("shows the list on <body> and puts it back by the input on close", () => {
    // Nested so there's somewhere other than <body> for the list to return to,
    // like the link modal it's really used in.
    document.body.innerHTML = '<div id="modal"><input id="nested-input"></div>';
    input = document.getElementById("nested-input");

    type("f", (term, cb) => cb([{ label: "Firefox" }]));
    expect(list().parentNode).to.equal(document.body);

    key("Escape");
    expect(list().parentNode.id).to.equal("modal");
    expect(input.nextElementSibling).to.equal(list());
  });

  it("closes the list when its handle is closed, without waiting for a blur", () => {
    const typeahead = attachTypeahead(input, (term, cb) => cb([{ label: "Firefox" }]));
    const clock = sinon.useFakeTimers();
    input.value = "f";
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300);
    clock.restore();
    expect(list().parentNode).to.equal(document.body);

    typeahead.close();
    expect(list().hidden).to.equal(true);
    expect(input.nextElementSibling).to.equal(list());
  });

  it("drops a search that hasn't gone out yet when the list is closed", () => {
    const source = sinon.spy();
    const typeahead = attachTypeahead(input, source, () => {});
    const clock = sinon.useFakeTimers();
    input.value = "fire";
    input.dispatchEvent(new window.Event("input"));
    typeahead.close(); // still inside the debounce window
    clock.tick(300);
    clock.restore();
    expect(source.called).to.equal(false);
  });

  it("ignores a response that lands after the list was closed", () => {
    document.body.innerHTML = '<div id="modal"><input id="nested-input"></div>';
    input = document.getElementById("nested-input");
    const responses = [];
    const typeahead = attachTypeahead(input, (term, cb) => responses.push(cb), () => {});
    const clock = sinon.useFakeTimers();
    input.value = "fire";
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300); // the search goes out
    clock.restore();

    typeahead.close();
    responses[0]([{ label: "Firefox" }]);

    // Nothing rendered, and nothing back on <body> where the dropdown shows.
    expect(list().hidden).to.equal(true);
    expect(list().children.length).to.equal(0);
    expect(list().parentNode.id).to.equal("modal");
  });

  it("returns a usable handle even without an input", () => {
    expect(() => attachTypeahead(null, () => {}).close()).to.not.throw();
  });

  it("follows the input while open and stops once closed", () => {
    const runFrames = fakeFrames();
    type("f", (term, cb) => cb([{ label: "Firefox" }]));
    const ul = list();
    const top = ul.style.top;

    // Nudge the list off its measured position: a scroll should measure again
    // and put it back.
    ul.style.top = "999px";
    window.dispatchEvent(new window.Event("scroll"));
    runFrames();
    expect(ul.style.top).to.equal(top);

    key("Escape");
    ul.style.top = "999px";
    window.dispatchEvent(new window.Event("scroll"));
    runFrames();
    expect(ul.style.top).to.equal("999px");
  });

  it("opens above the input when it doesn't fit below, right up against it", () => {
    // jsdom does no layout, so describe it ourselves: a 30px input near the
    // bottom of the 768px viewport, and a dropdown 90px tall.
    input.getBoundingClientRect = () => ({ top: 700, bottom: 730, left: 20, width: 200 });
    attachTypeahead(input, (term, cb) => cb([{ label: "Firefox" }]), () => {});
    Object.defineProperty(list(), "scrollHeight", { value: 90, configurable: true });

    const clock = sinon.useFakeTimers();
    input.value = "f";
    input.dispatchEvent(new window.Event("input"));
    clock.tick(300);
    clock.restore();

    // Pinned a gap above the input's top edge rather than a max-height above it.
    expect(list().style.top).to.equal("auto");
    expect(list().style.bottom).to.equal(window.innerHeight - 700 + 4 + "px");
  });

  it("hides the list while the input is scrolled out of its container", () => {
    document.body.innerHTML = '<div id="scroller"><input id="nested-input"></div>';
    input = document.getElementById("nested-input");
    const scroller = document.getElementById("scroller");
    // Again, jsdom won't lay this out: a container scrolled far enough that the
    // input has gone off the top of it.
    sinon
      .stub(window, "getComputedStyle")
      .callsFake((el) => ({ overflowY: el === scroller ? "auto" : "visible" }));
    scroller.getBoundingClientRect = () => ({ top: 100, bottom: 300 });
    input.getBoundingClientRect = () => ({ top: 40, bottom: 60, left: 0, width: 200 });

    type("f", (term, cb) => cb([{ label: "Firefox" }]));
    expect(list().hidden).to.equal(false);
    expect(list().style.visibility).to.equal("hidden");
  });

  it("points the input at the list and its active option", () => {
    type("f", (term, cb) => cb([{ label: "Firefox" }, { label: "Focus" }]));
    expect(input.getAttribute("role")).to.equal("combobox");
    expect(input.getAttribute("aria-controls")).to.equal(list().id);
    expect(input.getAttribute("aria-expanded")).to.equal("true");
    expect(list().getAttribute("role")).to.equal("listbox");
    expect(list().children[0].getAttribute("role")).to.equal("option");

    key("ArrowDown");
    expect(input.getAttribute("aria-activedescendant")).to.equal(list().children[0].id);
    expect(list().children[0].getAttribute("aria-selected")).to.equal("true");
    expect(list().children[1].getAttribute("aria-selected")).to.equal("false");

    key("Escape");
    expect(input.getAttribute("aria-expanded")).to.equal("false");
    expect(input.hasAttribute("aria-activedescendant")).to.equal(false);
  });
});

describe("markup: LinkButton article dropdown", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  function jsonResponse(body) {
    return {
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      text: async () => JSON.stringify(body),
    };
  }

  // Open the link modal and get the article dropdown showing.
  async function openModalWithSuggestions() {
    document.body.innerHTML = '<textarea id="id_content"></textarea>';
    sinon
      .stub(window, "fetch")
      .resolves(jsonResponse({ results: [{ title: "Firefox", url: "/kb/firefox" }] }));

    const btn = new Marky.LinkButton();
    btn.bind(document.getElementById("id_content"));
    btn.openModal({ preventDefault() {} });

    const internal = document.querySelector('#link-modal input[name="internal"]');
    const clock = sinon.useFakeTimers();
    internal.value = "fire";
    internal.dispatchEvent(new window.Event("input"));
    clock.tick(300); // the search runs on the far side of the debounce
    clock.restore();
    // Back on real timers, let the search's promises settle before we look.
    await new Promise((resolve) => setTimeout(resolve, 0));
    return internal;
  }

  it("shows suggestions outside the modal, where they won't be clipped", async () => {
    await openModalWithSuggestions();

    const list = document.querySelector("ul.marky-autocomplete");
    expect(list.parentNode).to.equal(document.body);
    expect(list.children[0].textContent).to.equal("Firefox");
  });

  it("takes the dropdown with it when the modal is dismissed", async () => {
    await openModalWithSuggestions();

    // Nothing here moves focus out of the input (jsdom won't, and neither will
    // some browsers), so the dropdown's own blur handling never runs.
    document.querySelector("#link-modal .kbox-cancel").click();

    expect(document.querySelector("#link-modal")).to.equal(null);
    expect(document.querySelector("ul.marky-autocomplete")).to.equal(null);
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

  it("opens the gallery in a new tab and closes the modal when Upload Image is clicked", () => {
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
