import { expect } from "chai";
import sinon from "sinon";

import Search from "sumo/js/search_utils";
import CachedXHR from "sumo/js/cached_xhr";

describe("search_utils Search", () => {
  afterEach(() => {
    sinon.restore();
    delete document.body.dataset.privateSearch;
  });

  it("stores params and serializes them", () => {
    const search = new Search("/api/1/kb/", { w: 1 });
    search.setParam("format", "json");

    expect(search.getParam("format")).to.equal("json");
    const serialized = search.serializeParams();
    expect(serialized).to.contain("w=1");
    expect(serialized).to.contain("format=json");

    search.unsetParam("format");
    expect(search.getParam("format")).to.equal(undefined);
  });

  it("query() requests via CachedXHR with the query merged into params", () => {
    const requestStub = sinon.stub(CachedXHR.prototype, "request");
    const search = new Search("/api/1/kb/", { w: 1 });
    const callback = () => {};
    const errorCallback = () => {};

    search.query("firefox", callback, errorCallback);

    expect(requestStub.calledOnce).to.equal(true);
    const [url, options] = requestStub.firstCall.args;
    expect(url).to.equal("/api/1/kb/");
    expect(options.data).to.deep.equal({ w: 1, q: "firefox" });
    expect(options.dataType).to.equal("json");
    expect(options.success).to.equal(callback);
    expect(options.error).to.equal(errorCallback);
    expect(search.lastQuery).to.equal("firefox");
  });

  [
    { privateSearch: false, cache: true },
    { privateSearch: true, cache: false },
  ].forEach(({ privateSearch, cache }) => {
    it(`query() ${cache ? "uses" : "skips"} the browser cache when private search is ${privateSearch}`, () => {
      const requestStub = sinon.stub(CachedXHR.prototype, "request");
      if (privateSearch) {
        document.body.dataset.privateSearch = "true";
      }

      new Search("/en-US/search/").query("vpn");

      expect(requestStub.firstCall.args[1].cache).to.equal(cache);
    });
  });
});

describe("CachedXHR", () => {
  afterEach(() => {
    sinon.restore();
    new CachedXHR().clearCache();
  });

  [
    { options: {}, requests: 1 },
    { options: { cache: false }, requests: 2 },
  ].forEach(({ options, requests }) => {
    it(`sends ${requests} request(s) for a repeated search with ${JSON.stringify(options)}`, async () => {
      const fetchStub = sinon.stub(window, "fetch").callsFake(async () => ({
        ok: true,
        status: 200,
        headers: { get: () => "application/json" },
        text: async () => '{"results": []}',
      }));
      const cxhr = new CachedXHR();

      for (let attempt = 0; attempt < 2; attempt++) {
        await new Promise((resolve, reject) => {
          cxhr.request("/en-US/search/", {
            cacheKey: "q=vpn",
            ...options,
            success: resolve,
            error: reject,
          });
        });
      }

      expect(fetchStub.callCount).to.equal(requests);
      expect(Object.keys(cxhr.dumpCache())).to.have.length(requests === 1 ? 1 : 0);
    });
  });
});
