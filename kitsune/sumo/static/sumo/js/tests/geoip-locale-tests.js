import { expect } from "chai";
import sinon from "sinon";

import { handleLocale } from "sumo/js/geoip-locale";

function jsonResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe("geoip-locale", () => {
  let originalLang;

  beforeEach(() => {
    originalLang = document.documentElement.lang;
    document.documentElement.lang = "en-US";
    sinon.stub(window, "fetch").resolves(
      jsonResponse({
        locales: { id: ["Indonesian", "Bahasa Indonesia"] },
        "en-US": { suggestion: "View in %(language)s?", confirm: "Yes", cancel: "No" },
        id: { suggestion: "Lihat %(language)s?", confirm: "Ya", cancel: "Tidak" },
      })
    );
    document.body.innerHTML =
      '<div id="announce-geoip-suggestion" class="mzp-c-notification-bar">' +
      '<button class="close-button"></button><p></p></div>';
  });

  afterEach(() => {
    window.fetch.restore();
    document.body.innerHTML = "";
    document.documentElement.lang = originalLang;
  });

  it("requests /geoip-suggestion with plain 'locales' params (no [])", () => {
    handleLocale("Indonesia");

    expect(window.fetch.calledOnce).to.equal(true);
    const url = window.fetch.firstCall.args[0];
    expect(url).to.contain("/geoip-suggestion?");
    expect(url).to.contain("locales=en-US");
    expect(url).to.contain("locales=id");
    expect(url).to.not.contain("locales%5B%5D");
  });

  it("removes the announce bar when no locale is suggested", () => {
    handleLocale("France");

    expect(window.fetch.called).to.equal(false);
    expect(document.getElementById("announce-geoip-suggestion")).to.equal(null);
  });
});
