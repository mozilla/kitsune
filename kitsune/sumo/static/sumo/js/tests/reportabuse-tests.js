import { expect } from "chai";
import sinon from "sinon";

import { init } from "sumo/js/reportabuse";

function jsonResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe("reportabuse", () => {
  let fetchStub;

  beforeEach(() => {
    fetchStub = sinon.stub(window, "fetch").resolves(jsonResponse({ message: "Reported!" }));
    document.body.innerHTML = `
      <a data-sumo-modal="ra">Report</a>
      <div data-modal-id="ra">
        <form action="/report" method="post">
          <input type="hidden" name="csrfmiddlewaretoken" value="tok">
          <input type="text" name="text" value="spam">
          <button type="submit">Send</button>
        </form>
        <div class="message"></div>
      </div>`;
    init();
  });

  afterEach(() => {
    window.fetch.restore();
    document.body.innerHTML = "";
  });

  it("POSTs the report to the form's action", () => {
    document.querySelector('[data-modal-id="ra"] [type="submit"]').click();

    expect(fetchStub.calledOnce).to.equal(true);
    const [url, init] = fetchStub.firstCall.args;
    expect(url).to.equal("/report");
    expect(init.method).to.equal("POST");
    expect(init.body).to.contain("text=spam");
  });

  it("shows the response message on success", async () => {
    document.querySelector('[data-modal-id="ra"] [type="submit"]').click();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(document.querySelector(".message").textContent).to.equal("Reported!");
  });
});
