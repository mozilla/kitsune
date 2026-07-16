import { expect } from "chai";
import sinon from "sinon";

import { ajaxSubmitInput, wrapDeleteInput } from "sumo/js/ajaxupload";

// ajaxupload.js calls the bare global `fetch` (not window.fetch), so these
// tests stub global.fetch. Ensure FormData/File resolve to jsdom's
// implementations in the node test bundle, mirroring mocha-require's Blob shim.
if (!global.FormData) {
  global.FormData = window.FormData;
}
if (!global.File) {
  global.File = window.File;
}
// wrapDeleteInput calls the bare global `confirm`; give it a stubbable default.
if (typeof global.confirm !== "function") {
  global.confirm = () => false;
}

function textResponse(text) {
  return { ok: true, status: 200, text: async () => text };
}

function failResponse(text) {
  return { ok: false, status: 500, text: async () => text };
}

function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("ajaxupload", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  describe("ajaxSubmitInput", () => {
    it("POSTs the selected file and CSRF token as FormData", async () => {
      document.body.innerHTML = `
        <form>
          <input type="hidden" name="csrfmiddlewaretoken" value="tok">
          <input type="file" name="image">
        </form>`;
      const fetchStub = sinon
        .stub(global, "fetch")
        .resolves(textResponse('{"status":"success"}'));
      const onComplete = sinon.spy();
      const input = document.querySelector('input[type="file"]');
      ajaxSubmitInput(input, { url: "/upload", onComplete });

      const file = new window.File(["x"], "pic.png", { type: "image/png" });
      Object.defineProperty(input, "files", { value: [file], configurable: true });
      input.dispatchEvent(new window.Event("change"));

      await tick();

      expect(fetchStub.calledOnce).to.equal(true);
      const [url, init] = fetchStub.firstCall.args;
      expect(url).to.equal("/upload");
      expect(init.method).to.equal("POST");
      expect(init.body).to.be.instanceOf(FormData);
      expect(init.body.get("csrfmiddlewaretoken")).to.equal("tok");
      expect(init.body.get("image")).to.not.equal(null);
      expect(onComplete.calledOnce).to.equal(true);
      expect(onComplete.firstCall.args[1]).to.equal('{"status":"success"}');
    });

    it("cancels the upload when beforeSubmit returns false", () => {
      document.body.innerHTML = '<form><input type="file" name="image"></form>';
      const fetchStub = sinon.stub(global, "fetch");
      const input = document.querySelector('input[type="file"]');
      ajaxSubmitInput(input, { url: "/upload", beforeSubmit: () => false });

      input.dispatchEvent(new window.Event("change"));

      expect(fetchStub.called).to.equal(false);
    });

    it("calls onComplete with null on a network error", async () => {
      document.body.innerHTML = '<form><input type="file" name="image"></form>';
      sinon.stub(global, "fetch").rejects(new Error("network"));
      const onComplete = sinon.spy();
      const input = document.querySelector('input[type="file"]');
      ajaxSubmitInput(input, { url: "/upload", onComplete });

      input.dispatchEvent(new window.Event("change"));
      await tick();

      expect(onComplete.calledOnce).to.equal(true);
      expect(onComplete.firstCall.args[1]).to.equal(null);
    });
  });

  describe("wrapDeleteInput", () => {
    function setupAttachment() {
      document.body.innerHTML = `
        <form>
          <input type="hidden" name="csrfmiddlewaretoken" value="tok">
          <div class="attachment">
            <img class="image" src="/x.png">
            <input type="button" class="delete" data-url="/delete/1">
          </div>
        </form>`;
      return document.querySelector("input.delete");
    }

    it("deletes the attachment on a successful response", async () => {
      const input = setupAttachment();
      sinon.stub(global, "confirm").returns(true);
      const fetchStub = sinon
        .stub(global, "fetch")
        .resolves(textResponse('{"status":"success"}'));
      const onComplete = sinon.spy();
      wrapDeleteInput(input, { onComplete });

      input.click();
      await tick();

      expect(fetchStub.calledOnce).to.equal(true);
      expect(fetchStub.firstCall.args[0]).to.equal("/delete/1");
      expect(document.querySelector(".attachment")).to.equal(null);
      expect(onComplete.calledOnce).to.equal(true);
    });

    it("does nothing when the user cancels the confirm", () => {
      const input = setupAttachment();
      sinon.stub(global, "confirm").returns(false);
      const fetchStub = sinon.stub(global, "fetch");
      wrapDeleteInput(input, {});

      input.click();

      expect(fetchStub.called).to.equal(false);
      expect(document.querySelector(".attachment")).to.not.equal(null);
    });

    it("keeps the attachment and shows a generic error on a network error", async () => {
      const input = setupAttachment();
      sinon.stub(global, "confirm").returns(true);
      sinon.stub(global, "fetch").rejects(new Error("network"));
      const onComplete = sinon.spy();
      wrapDeleteInput(input, { onComplete });

      input.click();
      await tick();

      expect(document.querySelector(".attachment")).to.not.equal(null);
      expect(document.querySelector(".image").style.opacity).to.equal("1");
      expect(onComplete.called).to.equal(false);
      expect(document.body.textContent).to.contain("There was an error");
    });

    it("shows a generic server error (not the sign-in hint) on a 500 with a non-JSON body", async () => {
      const input = setupAttachment();
      sinon.stub(global, "confirm").returns(true);
      sinon.stub(global, "fetch").resolves(failResponse("<h1>500 Server Error</h1>"));
      wrapDeleteInput(input, {});

      input.click();
      await tick();

      expect(document.querySelector(".attachment")).to.not.equal(null);
      expect(document.body.textContent).to.contain("There was an error");
      expect(document.body.textContent).to.not.contain("signed in");
    });

    it("shows the server's message on a non-2xx JSON error", async () => {
      const input = setupAttachment();
      sinon.stub(global, "confirm").returns(true);
      sinon
        .stub(global, "fetch")
        .resolves(
          failResponse(JSON.stringify({ status: "error", message: "You lack permission." }))
        );
      wrapDeleteInput(input, {});

      input.click();
      await tick();

      expect(document.querySelector(".attachment")).to.not.equal(null);
      expect(document.body.textContent).to.contain("You lack permission.");
    });

    it("shows the sign-in hint on an OK but unparseable (login redirect) response", async () => {
      const input = setupAttachment();
      sinon.stub(global, "confirm").returns(true);
      sinon.stub(global, "fetch").resolves(textResponse("<html>login page</html>"));
      wrapDeleteInput(input, {});

      input.click();
      await tick();

      expect(document.querySelector(".attachment")).to.not.equal(null);
      expect(document.body.textContent).to.contain("signed in");
    });
  });
});
