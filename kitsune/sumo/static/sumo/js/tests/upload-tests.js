import { expect } from "chai";
import sinon from "sinon";

import { init } from "sumo/js/upload";

// upload.js drives ajaxupload.js, which calls the bare global `fetch`; stub
// that. Ensure FormData/File resolve to jsdom's implementations in the node
// test bundle, mirroring mocha-require's Blob shim.
if (!global.FormData) {
  global.FormData = window.FormData;
}
if (!global.File) {
  global.File = window.File;
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

function setupUploadForm() {
  document.body.innerHTML = `
    <form>
      <input type="hidden" name="csrfmiddlewaretoken" value="tok">
      <div class="attachments-upload" data-post-url="/upload">
        <div class="upload-progress"></div>
        <div class="add-attachment"></div>
        <div class="adding-attachment"></div>
        <div class="uploaded"></div>
        <input type="file" name="image">
      </div>
    </form>`;
  init();
  const input = document.querySelector('input[type="file"]');
  const file = new window.File(["x"], "pic.png", { type: "image/png" });
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  return input;
}

describe("upload (async file upload)", () => {
  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("inserts an attachment on a successful upload", async () => {
    sinon.stub(global, "fetch").resolves(
      textResponse(
        JSON.stringify({
          status: "success",
          file: {
            name: "pic.png",
            url: "/img/1",
            width: "10",
            height: "10",
            thumbnail_url: "/thumb",
            delete_url: "/del/1",
          },
        })
      )
    );
    const input = setupUploadForm();

    input.dispatchEvent(new window.Event("change"));
    await tick();

    expect(document.querySelector(".attachment")).to.not.equal(null);
  });

  it("shows a generic server error (not the sign-in hint) on a 500 with a non-JSON body", async () => {
    sinon.stub(global, "fetch").resolves(failResponse("<h1>500 Server Error</h1>"));
    const input = setupUploadForm();

    input.dispatchEvent(new window.Event("change"));
    await tick();

    expect(document.querySelector(".attachment")).to.equal(null);
    expect(document.body.textContent).to.contain("There was an error");
    expect(document.body.textContent).to.not.contain("signed in");
  });

  it("shows the server's message on a non-2xx JSON error", async () => {
    sinon
      .stub(global, "fetch")
      .resolves(failResponse(JSON.stringify({ status: "error", message: "File too big." })));
    const input = setupUploadForm();

    input.dispatchEvent(new window.Event("change"));
    await tick();

    expect(document.body.textContent).to.contain("File too big.");
  });

  it("shows the sign-in hint on an OK but unparseable (login redirect) response", async () => {
    sinon.stub(global, "fetch").resolves(textResponse("<html>login page</html>"));
    const input = setupUploadForm();

    input.dispatchEvent(new window.Event("change"));
    await tick();

    expect(document.body.textContent).to.contain("signed in");
  });
});
