import { expect } from "chai";

import env from "sumo/js/nunjucks";

describe("nunjucks env", () => {
  it("urlparams filter merges params into the query string", () => {
    const urlparams = env.getFilter("urlparams");
    expect(urlparams("/x?a=1", { b: 2 })).to.equal("/x?a=1&b=2");
  });

  it("urlparams overrides an existing param", () => {
    const urlparams = env.getFilter("urlparams");
    expect(urlparams("/x?a=1", { a: 2 })).to.equal("/x?a=2");
  });

  it("urlparams returns undefined without a url", () => {
    const urlparams = env.getFilter("urlparams");
    expect(urlparams(undefined, { a: 1 })).to.equal(undefined);
  });
});
