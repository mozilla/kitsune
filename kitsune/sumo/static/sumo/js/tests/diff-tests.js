import { expect } from "chai";

import { initDiff } from "sumo/js/diff";

describe("diff", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("renders a diff table into .output", () => {
    document.body.innerHTML =
      '<div class="diff-this"><span class="from">abc</span>' +
      '<span class="to">abcd</span><div class="output"></div></div>';

    initDiff();

    const output = document.querySelector(".output");
    expect(output.querySelector(".diff-html")).to.not.equal(null);
    expect(output.querySelector("table")).to.not.equal(null);
  });

  it("shows 'No differences found' for identical text", () => {
    document.body.innerHTML =
      '<div class="diff-this"><span class="from">same</span>' +
      '<span class="to">same</span><div class="output"></div></div>';

    initDiff();

    expect(document.querySelector(".output").textContent).to.contain(
      "No differences found"
    );
  });
});
