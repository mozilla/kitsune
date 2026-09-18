import { expect } from "chai";

import { announceSignOutToOtherTabs, SIGN_OUT_KEY } from "sumo/js/sign-out-sync";

describe("sign-out-sync", () => {
  let form;

  beforeEach(() => {
    form = document.createElement("form");
    form.id = "sign-out";
    document.body.appendChild(form);
    window.localStorage.removeItem(SIGN_OUT_KEY);
  });

  afterEach(() => {
    form.remove();
    window.localStorage.removeItem(SIGN_OUT_KEY);
  });

  it("announces when the sign-out happened, so a later one still reads as a change", () => {
    // Storage events only fire on a change, so the value has to move each time.
    // Pinning it to the clock is what guarantees that.
    window.localStorage.setItem(SIGN_OUT_KEY, "1");
    const before = Date.now();
    announceSignOutToOtherTabs();

    form.dispatchEvent(new window.Event("submit"));

    const announced = Number(window.localStorage.getItem(SIGN_OUT_KEY));
    expect(announced).to.be.at.least(before);
    expect(announced).to.be.at.most(Date.now());
  });

  it("lets the sign-out go ahead", () => {
    announceSignOutToOtherTabs();

    const event = new window.Event("submit", { cancelable: true });
    form.dispatchEvent(event);

    expect(event.defaultPrevented).to.equal(false);
  });

  it("does nothing on a page with no sign-out form", () => {
    form.remove();

    announceSignOutToOtherTabs();

    expect(window.localStorage.getItem(SIGN_OUT_KEY)).to.equal(null);
  });
});
