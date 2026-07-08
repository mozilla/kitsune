import { expect } from "chai";
import sinon from "sinon";

import { apiFetch, getCsrfToken } from "sumo/js/utils/fetch";
import { setCookie, removeCookie } from "sumo/js/utils/cookie";

function fakeResponse({
  ok = true,
  status = 200,
  contentType = "application/json",
  body = "",
} = {}) {
  return {
    ok,
    status,
    headers: {
      get: (name) =>
        name.toLowerCase() === "content-type" ? contentType : null,
    },
    json: async () => (typeof body === "string" ? JSON.parse(body || "null") : body),
    text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
  };
}

describe("utils/fetch", () => {
  let fetchStub;

  beforeEach(() => {
    fetchStub = sinon.stub(window, "fetch");
    removeCookie("csrftoken");
    document.body.innerHTML = "";
  });

  afterEach(() => {
    window.fetch.restore();
    removeCookie("csrftoken");
    document.body.innerHTML = "";
  });

  describe("getCsrfToken", () => {
    it("prefers the csrftoken cookie", () => {
      setCookie("csrftoken", "from-cookie");
      document.body.innerHTML =
        '<input name="csrfmiddlewaretoken" value="from-input">';
      expect(getCsrfToken()).to.equal("from-cookie");
    });

    it("falls back to a csrfmiddlewaretoken input", () => {
      document.body.innerHTML =
        '<input name="csrfmiddlewaretoken" value="from-input">';
      expect(getCsrfToken()).to.equal("from-input");
    });
  });

  describe("apiFetch", () => {
    it("appends a data object as a query string on GET", async () => {
      fetchStub.resolves(fakeResponse({ body: { ok: 1 } }));
      await apiFetch("/search", { data: { q: "foo bar", page: 2 } });

      const [url, init] = fetchStub.firstCall.args;
      expect(url).to.equal("/search?q=foo+bar&page=2");
      expect(init.method).to.equal("GET");
      expect(init.body).to.equal(undefined);
      // no CSRF header on a safe method
      expect(init.headers["X-CSRFToken"]).to.equal(undefined);
    });

    it("form-encodes a data object and adds the CSRF header on POST", async () => {
      setCookie("csrftoken", "tok123");
      fetchStub.resolves(fakeResponse({ body: { message: "ok" } }));

      await apiFetch("/vote", {
        method: "POST",
        data: { helpful: "Yes", url: "/vote" },
      });

      const [url, init] = fetchStub.firstCall.args;
      expect(url).to.equal("/vote");
      expect(init.method).to.equal("POST");
      expect(init.headers["Content-Type"]).to.contain(
        "application/x-www-form-urlencoded"
      );
      expect(init.headers["X-CSRFToken"]).to.equal("tok123");
      expect(init.body).to.equal("helpful=Yes&url=%2Fvote");
    });

    it("parses a JSON response when dataType is json", async () => {
      fetchStub.resolves(fakeResponse({ body: { message: "hi" } }));
      const result = await apiFetch("/x", { dataType: "json" });
      expect(result).to.deep.equal({ message: "hi" });
    });

    it("returns text when dataType is html", async () => {
      fetchStub.resolves(
        fakeResponse({ contentType: "text/html", body: "<p>hi</p>" })
      );
      const result = await apiFetch("/x", { dataType: "html" });
      expect(result).to.equal("<p>hi</p>");
    });

    it("throws on a non-2xx response, exposing the response", async () => {
      fetchStub.resolves(
        fakeResponse({ ok: false, status: 500, contentType: "text/html", body: "boom" })
      );
      let error;
      try {
        await apiFetch("/x");
      } catch (e) {
        error = e;
      }
      expect(error).to.be.an("error");
      expect(error.response.status).to.equal(500);
    });
  });
});
