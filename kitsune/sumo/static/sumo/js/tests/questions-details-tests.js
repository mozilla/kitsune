import { expect } from "chai";
import sinon from "sinon";

import { initEditDetails } from "sumo/js/questions";

// A non-breaking space (U+00A0), the decoded form of the server's &nbsp;.
const NBSP = String.fromCharCode(160);

function jsonResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("questions: initEditDetails (topic dropdown)", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("renders nested-topic indentation as real spaces, not literal &nbsp;", async () => {
    document.body.innerHTML = `
      <select id="details-product">
        <option value="firefox" data-url="/products/firefox" selected>Firefox</option>
      </select>
      <select id="details-topic"></select>
      <button id="details-submit"></button>`;
    sinon.stub(window, "fetch").resolves(
      jsonResponse({
        topics: [
          { id: 1, title: "Top level" },
          { id: 2, title: "&nbsp;&nbsp;&nbsp;&nbsp;Subtopic" },
        ],
      })
    );

    initEditDetails();
    document
      .getElementById("details-product")
      .dispatchEvent(new window.Event("change"));
    await tick();

    const topic = document.getElementById("details-topic");
    expect(topic.options.length).to.equal(2);
    // The server prefixes nested topics with &nbsp; entities for indentation;
    // they must be decoded to real non-breaking spaces, not shown literally.
    expect(topic.options[1].textContent).to.equal(NBSP.repeat(4) + "Subtopic");
    expect(topic.options[1].textContent).to.not.contain("&nbsp;");
  });
});
