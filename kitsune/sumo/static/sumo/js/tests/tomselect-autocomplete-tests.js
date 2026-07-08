import { expect } from "chai";
import sinon from "sinon";

import { initRecipientAutocomplete } from "sumo/js/tomselect-autocomplete";
import { renderUserOption } from "sumo/js/users.autocomplete";
import { renderSuggestion } from "sumo/js/messages.autocomplete";

// Minimal HTML-escaper matching what Tom Select passes to render functions.
function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function jsonResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe("tomselect-autocomplete", () => {
  describe("renderUserOption", () => {
    it("shows display_name [username] with an avatar", () => {
      const html = renderUserOption(
        { avatar: "/a.png", display_name: "Bob B", username: "bob" },
        esc
      );
      expect(html).to.contain('class="avatar"');
      expect(html).to.contain("/a.png");
      expect(html).to.contain("Bob B [bob]");
    });

    it("shows just the username when there is no display_name", () => {
      const html = renderUserOption(
        { avatar: "/a.png", display_name: null, username: "bob" },
        esc
      );
      expect(html).to.contain(">bob</div>");
      expect(html).to.not.contain("[");
    });

    it("escapes user-controlled content", () => {
      const html = renderUserOption(
        { avatar: "/a.png", display_name: null, username: "<b>x</b>" },
        esc
      );
      expect(html).to.not.contain("<b>x</b>");
      expect(html).to.contain("&lt;b&gt;x&lt;/b&gt;");
    });
  });

  describe("renderSuggestion", () => {
    it("renders the type icon, avatar, name, and type class", () => {
      const html = renderSuggestion(
        {
          type: "User",
          type_icon: "/u.svg",
          avatar: "/a.png",
          name: "bob",
          display_name: "Bob",
        },
        esc
      );
      expect(html).to.contain('class="User"');
      expect(html).to.contain("/u.svg");
      expect(html).to.contain("/a.png");
      expect(html).to.contain("bob");
    });
  });

  describe("initRecipientAutocomplete", () => {
    afterEach(() => {
      // Restores everything installed via sinon in a test (the window.fetch
      // stub AND any fake timers), even if an assertion threw first.
      sinon.restore();
      document.body.innerHTML = "";
    });

    it("prefills selected items from the input's comma-separated value", () => {
      document.body.innerHTML =
        '<form><input class="user-autocomplete" name="to" value="bob,alice"></form>';
      const input = document.querySelector("input.user-autocomplete");
      const ts = initRecipientAutocomplete(input, {
        apiUrl: "/api/usernames",
        valueField: "username",
        labelField: "username",
        renderOption: renderUserOption,
      });
      expect(ts.getValue()).to.equal("bob,alice");
      ts.destroy();
    });

    it("loads suggestions from the API using the term query param", () => {
      const fetchStub = sinon
        .stub(window, "fetch")
        .resolves(jsonResponse([{ username: "bob", display_name: "Bob", avatar: "/a.png" }]));
      document.body.innerHTML =
        '<form><input class="user-autocomplete" name="to"></form>';
      const input = document.querySelector("input.user-autocomplete");
      const ts = initRecipientAutocomplete(input, {
        apiUrl: "/api/usernames",
        valueField: "username",
        labelField: "username",
        renderOption: renderUserOption,
      });

      // Tom Select debounces load() by its loadThrottle (default 300ms), so
      // advance fake timers past it to exercise the real Tom Select -> load ->
      // apiFetch -> fetch path. The clock is restored in afterEach.
      const clock = sinon.useFakeTimers();
      ts.load("bo");
      clock.tick(400);

      expect(fetchStub.calledOnce).to.equal(true);
      expect(fetchStub.firstCall.args[0]).to.contain("/api/usernames?term=bo");
      ts.destroy();
    });

    it("keeps a comma-joined value as items are added (submission format)", () => {
      document.body.innerHTML =
        '<form><input class="user-autocomplete" name="to"></form>';
      const input = document.querySelector("input.user-autocomplete");
      const ts = initRecipientAutocomplete(input, {
        apiUrl: "/api/usernames",
        valueField: "username",
        labelField: "username",
        renderOption: renderUserOption,
      });

      ts.addOption({ username: "bob" });
      ts.addItem("bob");
      ts.addOption({ username: "alice" });
      ts.addItem("alice");

      expect(ts.getValue()).to.equal("bob,alice");
      ts.destroy();
    });
  });
});
