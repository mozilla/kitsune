import { expect } from "chai";

import Marky from "sumo/js/markup";

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
