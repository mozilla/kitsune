import { expect } from "chai";

import { initSummaryCount } from "sumo/js/wiki";
import { initCharacterCounter } from "sumo/js/messages";

function type(input, length) {
  input.value = "x".repeat(length);
  input.dispatchEvent(new window.Event("input"));
}

describe("character counters", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("toggle is-over-limit past their limits instead of setting an inline color", () => {
    document.body.innerHTML = `
      <input id="id_summary">
      <span id="remaining-characters">1000</span>`;
    initSummaryCount();
    const summary = document.getElementById("id_summary");
    const summaryCount = document.getElementById("remaining-characters");

    type(summary, 161);
    expect(summaryCount.classList.contains("is-over-limit")).to.equal(true);
    type(summary, 160);
    expect(summaryCount.classList.contains("is-over-limit")).to.equal(false);
    expect(summaryCount.style.color).to.equal("");

    document.body.innerHTML = `
      <textarea id="id_message"></textarea>
      <div id="remaining-characters" data-max-characters="100" data-input="#id_message"></div>`;
    initCharacterCounter();
    const message = document.getElementById("id_message");
    const messageCount = document.getElementById("remaining-characters");

    type(message, 91);
    expect(messageCount.classList.contains("is-over-limit")).to.equal(true);
    type(message, 90);
    expect(messageCount.classList.contains("is-over-limit")).to.equal(false);
    expect(messageCount.style.color).to.equal("");
  });
});
