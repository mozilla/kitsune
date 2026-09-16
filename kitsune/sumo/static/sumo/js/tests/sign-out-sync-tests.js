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

  it("announces a sign-out for the other tabs to hear", () => {
    announceSignOutToOtherTabs();

    form.dispatchEvent(new window.Event("submit"));

    expect(window.localStorage.getItem(SIGN_OUT_KEY)).to.match(/^\d+$/);
  });

  it("writes a new value each time, so a later sign-out still reads as a change", () => {
    window.localStorage.setItem(SIGN_OUT_KEY, "1");
    announceSignOutToOtherTabs();

    form.dispatchEvent(new window.Event("submit"));

    expect(window.localStorage.getItem(SIGN_OUT_KEY)).to.not.equal("1");
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
