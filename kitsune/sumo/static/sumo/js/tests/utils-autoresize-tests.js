import { expect } from "chai";

import { autoResize } from "sumo/js/utils/autoresize";

describe("utils/autoresize", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("applies minHeight and disables manual resize", () => {
    document.body.innerHTML = '<textarea id="ta"></textarea>';
    const ta = document.getElementById("ta");

    autoResize(ta, { minHeight: 150 });

    // jsdom reports scrollHeight 0 (no layout), so the min applies.
    expect(ta.style.height).to.equal("150px");
    expect(ta.style.resize).to.equal("none");
    expect(ta.style.overflowY).to.equal("hidden");
  });

  it("re-measures on input", () => {
    document.body.innerHTML = '<textarea id="ta"></textarea>';
    const ta = document.getElementById("ta");
    autoResize(ta, { minHeight: 100 });

    // Force a taller measurement, then dispatch input.
    Object.defineProperty(ta, "scrollHeight", { value: 320, configurable: true });
    ta.dispatchEvent(new window.Event("input"));

    expect(ta.style.height).to.equal("320px");
  });

  it("caps at maxHeight and enables scrolling", () => {
    document.body.innerHTML = '<textarea id="ta"></textarea>';
    const ta = document.getElementById("ta");
    Object.defineProperty(ta, "scrollHeight", { value: 999, configurable: true });

    autoResize(ta, { minHeight: 100, maxHeight: 500 });

    expect(ta.style.height).to.equal("500px");
    expect(ta.style.overflowY).to.equal("auto");
  });

  it("returns the element (or the falsy arg unchanged)", () => {
    document.body.innerHTML = '<textarea id="ta"></textarea>';
    const ta = document.getElementById("ta");
    expect(autoResize(ta)).to.equal(ta);
    expect(autoResize(null)).to.equal(null);
  });
});
