import { expect } from "chai";

import { userMessageUI, initAutoSubmitSelects } from "sumo/js/main";

describe("main: userMessageUI", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    localStorage.clear();
  });

  it("adds a close button to each user message", () => {
    document.body.innerHTML = `
      <ul class="user-messages">
        <li id="m1">one</li>
        <li id="m2">two</li>
      </ul>`;
    userMessageUI();
    expect(
      document.querySelectorAll(".user-messages > li .close-button")
    ).to.have.length(2);
  });

  it("dismisses a dismissible message and remembers it", () => {
    document.body.innerHTML = `
      <ul class="user-messages">
        <li id="d1" class="dismissible"><button class="dismiss">x</button></li>
      </ul>`;
    userMessageUI();

    const msg = document.getElementById("d1");
    msg.querySelector(".dismiss").click();

    expect(msg.style.display).to.equal("none");
    expect(localStorage.getItem("user-message::dismissed::d1")).to.equal("true");
  });
});

describe("main: initAutoSubmitSelects", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("submits the form when an autosubmit select changes", () => {
    document.body.innerHTML = `
      <form id="f">
        <select class="autosubmit"><option>a</option><option>b</option></select>
      </form>`;
    initAutoSubmitSelects();

    let submitted = false;
    document.getElementById("f").addEventListener("submit", (e) => {
      e.preventDefault();
      submitted = true;
    });

    document
      .querySelector("select.autosubmit")
      .dispatchEvent(new window.Event("change"));

    expect(submitted).to.equal(true);
  });
});
