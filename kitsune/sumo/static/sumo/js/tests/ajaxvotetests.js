import React from 'react';
import {expect} from 'chai';
import sinon from 'sinon';

import AjaxVote from "sumo/js/ajaxvote";

describe('ajaxvote', () => {
  describe('helpful vote', () => {
    beforeEach(() => {
      sinon.stub($, 'ajax').yieldsTo('success', {message: 'Thanks for the vote!'});

      let sandbox = (
        <form className="vote" action="/vote" method="post">
          <input type="submit" name="helpful" defaultValue="Yes" />
          <input type="submit" name="not-helpful" defaultValue="No" />
        </form>
      );
      React.render(sandbox, document.body);
    });

    afterEach(() => {
      $.ajax.restore();
      React.unmountComponentAtNode(document.body);
      $(document).off('vote');
    });

    it('should fire an event on a helpful vote', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      $(document).on('vote', (ev, data) => {
        expect(data.helpful).to.equal('Yes');
        expect(data.url).to.equal('/vote');
        done();
      });
      $('input[name="helpful"]').on("click", );
    });

    it('should fire an event on an unhelpful vote', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      $(document).on('vote', (ev, data) => {
        expect(data['not-helpful']).to.equal('No');
        expect(data.url).to.equal('/vote');
        done();
      });
      $('input[name="not-helpful"]').trigger('click');
    });

    it('should include the right data in the request', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      $(document).on('vote', (ev, data) => {
        expect($.ajax.calledOnce).to.equal(true);
        expect($.ajax.firstCall.args[0].data.helpful).to.equal('Yes');
        done();
      });
      $('input[name="helpful"]').trigger('click');
    });

    it('should update the UI with the response', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      $(document).on('vote', (ev, data) => {
        expect($('.ajax-vote-box').text()).to.equal('Thanks for the vote!');
        done();
      });
      $('input[name="helpful"]').trigger('click');
    });

  });
});
