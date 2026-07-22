import { expect } from "chai";

import { getCookie, setCookie, removeCookie } from "sumo/js/utils/cookie";

describe("utils/cookie", () => {
  afterEach(() => {
    // Clean up any cookies the tests set so they don't leak between specs.
    ["c_read", "c write", "c_gone", "csrftoken"].forEach((name) =>
      removeCookie(name)
    );
  });

  describe("getCookie", () => {
    it("returns the value of a cookie", () => {
      document.cookie = "c_read=hello";
      expect(getCookie("c_read")).to.equal("hello");
    });

    it("returns undefined for a missing cookie", () => {
      expect(getCookie("does_not_exist")).to.equal(undefined);
    });

    it("decodes url-encoded names and values", () => {
      setCookie("c write", "a b&c");
      expect(getCookie("c write")).to.equal("a b&c");
    });
  });

  describe("setCookie / removeCookie", () => {
    it("round-trips a value through setCookie/getCookie", () => {
      setCookie("c_read", "value1");
      expect(getCookie("c_read")).to.equal("value1");
    });

    it("removeCookie deletes the cookie", () => {
      setCookie("c_gone", "temp");
      expect(getCookie("c_gone")).to.equal("temp");
      removeCookie("c_gone");
      expect(getCookie("c_gone")).to.equal(undefined);
    });
  });
});
