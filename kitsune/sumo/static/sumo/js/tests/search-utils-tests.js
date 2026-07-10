import { expect } from "chai";
import sinon from "sinon";

import Search from "sumo/js/search_utils";
import CachedXHR from "sumo/js/cached_xhr";

describe("search_utils Search", () => {
  afterEach(() => {
    sinon.restore();
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

    search.query("firefox", callback);

    expect(requestStub.calledOnce).to.equal(true);
    const [url, options] = requestStub.firstCall.args;
    expect(url).to.equal("/api/1/kb/");
    expect(options.data).to.deep.equal({ w: 1, q: "firefox" });
    expect(options.dataType).to.equal("json");
    expect(options.success).to.equal(callback);
    expect(search.lastQuery).to.equal("firefox");
  });
});
