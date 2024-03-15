import {expect} from 'chai';
import sinon from 'sinon';

import AjaxVote from "sumo/js/ajaxvote";

describe('ajaxvote', () => {
  let eventListener;

  describe('helpful vote', () => {
    beforeEach(() => {
      sinon.stub($, 'ajax').yieldsTo('success', {message: 'Thanks for the vote!'});
      $('body').empty().html(`
        <form class="vote" action="/vote" method="post">
          <input type="submit" name="helpful" value="Yes">
          <input type="submit" name="not-helpful" value="No">
        </form>`
      );
    });

    afterEach(() => {
      $.ajax.restore();
      document.removeEventListener('vote', eventListener);
    });

    it('should fire an event on a helpful vote', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect(event.detail.helpful).to.equal('Yes');
        expect(event.detail.url).to.equal('/vote');
        done();
      }
      document.addEventListener('vote', eventListener);
      $('input[name="helpful"]').trigger("click");
    });

    it('should fire an event on an unhelpful vote', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect(event.detail['not-helpful']).to.equal('No');
        expect(event.detail.url).to.equal('/vote');
        done();
      }
      document.addEventListener('vote', eventListener);
      $('input[name="not-helpful"]').trigger('click');
    });

    it('should include the right data in the request', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect($.ajax.calledOnce).to.equal(true);
        expect($.ajax.firstCall.args[0].data.helpful).to.equal('Yes');
        done();
      }
      document.addEventListener('vote', eventListener);
      $('input[name="helpful"]').trigger('click');
    });

    it('should update the UI with the response', done => {
      let ajaxVote = new AjaxVote($('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect($('.ajax-vote-box').text()).to.equal('Thanks for the vote!');
        done();
      }
      document.addEventListener('vote', eventListener);
      $('input[name="helpful"]').trigger('click');
    });

  });
});
