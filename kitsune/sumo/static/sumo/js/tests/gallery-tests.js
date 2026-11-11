import { expect } from "chai";
import sinon from "sinon";

import { GalleryUpload } from "sumo/js/gallery";

// The upload modal as rendered for a user who chooses who can see the image.
const MODAL = `
  <div class="gallery-upload-modal" id="gallery-upload-modal" data-max-image-size="1048576">
    <form id="gallery-upload-image" class="upload-form" data-post-url="/gallery/image/upload_async"
      method="post" enctype="multipart/form-data" action="/gallery/images/upload" data-file="0">
      <input type="hidden" name="csrfmiddlewaretoken" value="tok">
      <div class="field knowledge_base knowledge-base">
        <select name="knowledge_base" required>
          <option value="" selected>Choose…</option>
          <option value="public">Everyone (public)</option>
          <optgroup label="Readers of a private knowledge base">
            <option value="7">Foo</option>
          </optgroup>
        </select>
      </div>
      <div class="field file upload-media">
        <input type="file" name="file">
        <div class="details help-text">Accepted formats include .PNG, .JPG, .JPEG and .GIF.</div>
      </div>
      <div class="field progress file">
        <div class="progress-message"></div>
        <a class="file sumo-button" data-type="file" href="/gallery/images">Cancel</a>
      </div>
      <div class="field preview file off">
        <div class="preview-image file"></div>
        <input type="submit" name="cancel" class="sumo-button button-sm draft link-btn"
          data-name="file" data-action="/gallery/images/cancel_draft" value="Delete this image">
      </div>
      <div class="field title metadata"><input type="text" name="title"></div>
      <div class="upload-action">
        <input type="submit" class="sumo-button primary-button" name="upload" value="Upload">
        <input type="submit" name="cancel" class="sumo-button kbox-cancel"
          data-action="/gallery/images/cancel_draft" value="Cancel">
      </div>
    </form>
  </div>`;

const UPLOADED = JSON.stringify({
  status: "success",
  file: { name: "pic.png", thumbnail_url: "/private-media/private/uploads/pic.png" },
});

function response(text) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    text: async () => text,
    json: async () => JSON.parse(text),
  };
}

function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function choice() {
  return document.querySelector('select[name="knowledge_base"]');
}

function details() {
  return document.querySelector(".upload-media.file .details");
}

// jsdom can't set a file input's files or value, so give the input its own.
function selectFile() {
  const input = document.querySelector('input[type="file"]');
  let value = "C:\\fakepath\\pic.png";
  Object.defineProperty(input, "value", {
    get: () => value,
    set: (newValue) => {
      value = newValue;
    },
    configurable: true,
  });
  const file = new window.File(["x"], "pic.png", { type: "image/png" });
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  input.dispatchEvent(new window.Event("change"));
  return input;
}

describe("gallery upload: knowledge base choice", () => {
  let uploadFetch;

  function freshModal() {
    document.body.innerHTML = MODAL;
    GalleryUpload.init();
  }

  beforeEach(() => {
    // ajaxupload POSTs with the bare fetch, apiFetch (cancel_draft) with window.fetch.
    uploadFetch = sinon.stub(global, "fetch").resolves(response(UPLOADED));
    sinon.stub(window, "fetch").resolves(response('{"status": "success"}'));
    freshModal();
  });

  afterEach(() => {
    sinon.restore();
    document.body.innerHTML = "";
  });

  it("blocks the upload until who can see the image is chosen", async () => {
    const input = selectFile();
    await tick();

    expect(uploadFetch.called).to.equal(false);
    expect(input.value).to.equal("");
    expect(details().textContent).to.equal(
      "Please choose who can see the image, then select the image again."
    );
    expect(choice().disabled).to.equal(false);
  });

  it("sends the choice with the file and locks it once the upload starts", async () => {
    choice().value = "7";

    selectFile();

    expect(choice().disabled).to.equal(true);
    await tick();
    expect(uploadFetch.firstCall.args[1].body.get("knowledge_base")).to.equal("7");
    expect(choice().disabled).to.equal(true);
  });

  it("unlocks the choice when the upload is cancelled or deleted, or the modal closed", async () => {
    const cases = [
      { name: "cancel", pending: true, act: () => document.querySelector(".progress a").click() },
      { name: "delete", act: () => document.querySelector('.preview input[name="cancel"]').click() },
      { name: "close", act: () => GalleryUpload.modalClose(), resets: true },
    ];
    for (const { name, pending, act, resets } of cases) {
      freshModal();
      if (pending) {
        uploadFetch.returns(new Promise(() => {}));
      } else {
        uploadFetch.resolves(response(UPLOADED));
      }
      choice().value = "7";
      selectFile();
      await tick();
      expect(choice().disabled).to.equal(true, name);

      act();

      expect(choice().disabled).to.equal(false, name);
      if (resets) {
        expect(choice().value).to.equal("", name);
      }
    }
  });

  it("shows the server's reason for a rejected upload unless it reports field errors", async () => {
    const invalid = "Invalid image. Please select a valid image file.";
    const cases = [
      [
        '{"status": "error", "message": "Please choose who can see the image."}',
        "Please choose who can see the image.",
      ],
      [
        '{"status": "error", "message": "Could not upload your image.", "errors": {"file": ["Corrupt"]}}',
        invalid,
      ],
      ['{"status": "error"}', invalid],
      ["<html>", "Could not upload file. Please try again later."],
    ];
    for (const [body, shown] of cases) {
      freshModal();
      uploadFetch.resolves(response(body));
      choice().value = "7";
      selectFile();
      await tick();

      expect(details().textContent).to.equal(shown, body);
      expect(choice().disabled).to.equal(false, body);
    }
  });
});
