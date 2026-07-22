import { expect } from "chai";

import { fadeOut, fadeIn, slideUp, slideDown, slideToggle, serialize, toElements, toElement } from "sumo/js/utils/dom";

describe("utils/dom", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  describe("toElements / toElement", () => {
    beforeEach(() => {
      document.body.innerHTML =
        '<div class="a" id="one"></div><div class="a" id="two"></div>';
    });

    it("resolves a selector string to all matches", () => {
      const els = toElements(".a");
      expect(els.map((el) => el.id)).to.deep.equal(["one", "two"]);
    });

    it("wraps a single DOM node", () => {
      const el = document.getElementById("one");
      expect(toElements(el)).to.deep.equal([el]);
    });

    it("converts an array-like (NodeList / jQuery object) to an array", () => {
      const nodeList = document.querySelectorAll(".a");
      // A jQuery object is also array-like with a numeric length + indices.
      const jqueryLike = { 0: nodeList[0], 1: nodeList[1], length: 2 };
      expect(toElements(nodeList)).to.have.length(2);
      expect(toElements(jqueryLike)).to.deep.equal([nodeList[0], nodeList[1]]);
    });

    it("returns [] for null/undefined and the first match for toElement", () => {
      expect(toElements(null)).to.deep.equal([]);
      expect(toElement(".a").id).to.equal("one");
      expect(toElement(null)).to.equal(null);
    });
  });

  describe("fadeOut", () => {
    it("hides the element and resolves", async () => {
      document.body.innerHTML = '<div id="box">hi</div>';
      const box = document.getElementById("box");
      await fadeOut(box, 1);
      expect(box.style.display).to.equal("none");
    });
  });

  describe("slideUp", () => {
    it("collapses the element and sets display:none", async () => {
      document.body.innerHTML = '<div id="box">content</div>';
      const box = document.getElementById("box");
      await slideUp(box, 1);
      expect(box.style.display).to.equal("none");
    });
  });

  describe("fadeIn", () => {
    it("makes a hidden element visible and resolves", async () => {
      document.body.innerHTML = '<div id="box" style="display:none">hi</div>';
      const box = document.getElementById("box");
      await fadeIn(box, 1);
      expect(box.style.display).to.not.equal("none");
    });
  });

  describe("slideDown", () => {
    it("reveals a hidden element and resolves", async () => {
      document.body.innerHTML = '<div id="box" style="display:none">content</div>';
      const box = document.getElementById("box");
      await slideDown(box, 1);
      expect(box.style.display).to.not.equal("none");
    });
  });

  describe("slideToggle", () => {
    it("shows a hidden element and hides a visible one", async () => {
      document.body.innerHTML = '<div id="box" style="display:none">content</div>';
      const box = document.getElementById("box");
      await slideToggle(box, 1);
      expect(box.style.display).to.not.equal("none");
      await slideToggle(box, 1);
      expect(box.style.display).to.equal("none");
    });
  });

  describe("serialize", () => {
    it("collects successful controls, skipping buttons and unchecked boxes", () => {
      document.body.innerHTML = `
        <form>
          <input name="title" value="Hello">
          <input type="checkbox" name="agree" value="yes" checked>
          <input type="checkbox" name="spam" value="no">
          <input type="radio" name="color" value="red">
          <input type="radio" name="color" value="blue" checked>
          <input type="submit" name="save" value="Save">
          <input name="disabled_field" value="nope" disabled>
          <textarea name="body">text</textarea>
        </form>`;
      const form = document.querySelector("form");
      expect(serialize(form)).to.deep.equal({
        title: "Hello",
        agree: "yes",
        color: "blue",
        body: "text",
      });
    });

    it("collapses repeated names into an array", () => {
      document.body.innerHTML = `
        <form>
          <input type="checkbox" name="tag" value="a" checked>
          <input type="checkbox" name="tag" value="b" checked>
        </form>`;
      const form = document.querySelector("form");
      expect(serialize(form)).to.deep.equal({ tag: ["a", "b"] });
    });
  });
});
