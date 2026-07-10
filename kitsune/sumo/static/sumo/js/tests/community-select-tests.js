import { expect } from "chai";

import { init } from "community/js/select";

describe("community/select", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="selector">
        <button type="button" class="ts-select-trigger">Choose</button>
        <div class="select-options" aria-expanded="false">
          <ul class="ts-options" tabindex="-1">
            <li><a class="option-a">Option A</a></li>
            <li><a class="option-b">Option B</a></li>
          </ul>
        </div>
      </div>`;
    init();
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("expands the options when the trigger is clicked", () => {
    const container = document.querySelector(".select-options");
    expect(container.getAttribute("aria-expanded")).to.equal("false");

    document.querySelector(".ts-select-trigger").click();

    expect(container.getAttribute("aria-expanded")).to.equal("true");
  });

  it("marks the clicked option selected and clears the others", () => {
    const a = document.querySelector(".option-a");
    const b = document.querySelector(".option-b");

    a.click();
    expect(a.classList.contains("selected")).to.equal(true);
    expect(a.getAttribute("aria-checked")).to.equal("true");

    b.click();
    expect(b.classList.contains("selected")).to.equal(true);
    expect(a.classList.contains("selected")).to.equal(false);
    expect(a.hasAttribute("aria-checked")).to.equal(false);
  });
});
