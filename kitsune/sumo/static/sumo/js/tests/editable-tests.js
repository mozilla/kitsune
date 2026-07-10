import { expect } from "chai";

import { initInlineEditing } from "sumo/js/editable";

describe("editable", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("toggles the edit-on class and the link text", () => {
    document.body.innerHTML = '<div class="editable"><a class="edit">Edit</a></div>';
    initInlineEditing();

    const edit = document.querySelector("a.edit");
    const container = document.querySelector(".editable");

    edit.click();
    expect(container.classList.contains("edit-on")).to.equal(true);
    expect(edit.textContent).to.equal("Cancel");

    edit.click();
    expect(container.classList.contains("edit-on")).to.equal(false);
    expect(edit.textContent).to.equal("Edit");
  });
});
