import React from 'react';
import {expect} from 'chai';
import sinon from 'sinon';

import AjaxPreview from "sumo/js/ajaxpreview";

describe('ajax preview', () => {
  describe('events', () => {

    beforeEach(() => {

      sinon.stub($, 'ajax').yieldsTo('success', '<p>The content to preview.</p>');

      let sandbox = (
        <div>
          <form action="" method="post">
            <input type="hidden" name="csrfmiddlewaretoken" defaultValue="tokenvalue" />
            <textarea id="id_content" name="content" defaultValue="The content to preview."/>
            <input type="submit" id="preview" name="preview" defaultValue="Preview"
              data-preview-url="/preview"
              data-preview-container-id="preview-container"
              data-preview-content-id="id_content" />
          </form>
          <div id="preview-container"></div>
        </div>
      );
      React.render(sandbox, window.document.body);
    });

    afterEach(() => {
      $.ajax.restore();
      React.unmountComponentAtNode(window.document.body);
    });

    // This test is mainly about testing the test framework.
    it('should have a jquery', () => {
      expect($('body').length).to.equal(1);
    });

    it('should fire "show-preview" event', done => {
      let ajaxPreview = new AjaxPreview($('#preview'));
      $(ajaxPreview).bind('show-preview', (e, success, content) => {
        expect(success).to.equal(true);
        expect(content).to.equal('<p>The content to preview.</p>');
        done();
      });
      $(ajaxPreview).trigger('get-preview');
    });

    it('should fire "done" event', done => {
      let ajaxPreview = new AjaxPreview($('#preview'));
      $(ajaxPreview).bind('done', (e, success) => {
        expect(success).to.equal(true);
        done();
      });
      $(ajaxPreview).trigger('get-preview');
    });

    it('should show the preview', done => {
      let ajaxPreview = new AjaxPreview($('#preview'));
      $(ajaxPreview).bind('done', (e, success) => {
        expect($('#preview-container').html())
          .to.equal('<p>The content to preview.</p>');
        done();
      });
      $('#preview').trigger('click');
    });
  });
});
