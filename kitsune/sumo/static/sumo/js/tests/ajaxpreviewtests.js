import {expect} from 'chai';
import sinon from 'sinon';

import AjaxPreview from "sumo/js/ajaxpreview";

function htmlResponse(html) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "text/html" },
    json: async () => JSON.parse(html),
    text: async () => html,
  };
}

describe('ajax preview', () => {
  describe('events', () => {

    beforeEach(() => {
      sinon
        .stub(window, 'fetch')
        .resolves(htmlResponse('<p>The content to preview.</p>'));

      document.body.innerHTML = `
        <div>
          <form action="" method="post">
            <input type="hidden" name="csrfmiddlewaretoken" value="tokenvalue">
            <textarea id="id_content" name="content"></textarea>
            <input type="submit" id="preview" name="preview" value="Preview"
              data-preview-url="/preview"
              data-preview-container-id="preview-container"
              data-preview-content-id="id_content">
          </form>
          <div id="preview-container"></div>
        </div>`;
    });

    afterEach(() => {
      window.fetch.restore();
      document.body.innerHTML = '';
    });

    it('should fire "show-preview" event', done => {
      let ajaxPreview = new AjaxPreview(document.getElementById('preview'));
      ajaxPreview.addEventListener('show-preview', (e) => {
        expect(e.detail.success).to.equal(true);
        expect(e.detail.html).to.equal('<p>The content to preview.</p>');
        done();
      });
      ajaxPreview.dispatchEvent(new CustomEvent('get-preview'));
    });

    it('should fire "done" event', done => {
      let ajaxPreview = new AjaxPreview(document.getElementById('preview'));
      ajaxPreview.addEventListener('done', (e) => {
        expect(e.detail.success).to.equal(true);
        done();
      });
      ajaxPreview.dispatchEvent(new CustomEvent('get-preview'));
    });

    it('should show the preview', done => {
      let ajaxPreview = new AjaxPreview(document.getElementById('preview'));
      ajaxPreview.addEventListener('done', () => {
        expect(document.getElementById('preview-container').innerHTML)
          .to.equal('<p>The content to preview.</p>');
        done();
      });
      document.getElementById('preview').click();
    });
  });
});
