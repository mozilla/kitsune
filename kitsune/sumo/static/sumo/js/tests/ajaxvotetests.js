import {expect} from 'chai';
import sinon from 'sinon';

import AjaxVote from "sumo/js/ajaxvote";

function jsonResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe('ajaxvote', () => {
  let eventListener;
  let fetchStub;

  describe('helpful vote', () => {
    beforeEach(() => {
      fetchStub = sinon
        .stub(window, 'fetch')
        .resolves(jsonResponse({message: 'Thanks for the vote!'}));
      document.body.innerHTML = `
        <form class="vote" action="/vote" method="post">
          <input type="submit" name="helpful" value="Yes">
          <input type="submit" name="not-helpful" value="No">
        </form>`;
    });

    afterEach(() => {
      window.fetch.restore();
      document.removeEventListener('vote', eventListener);
      document.body.innerHTML = '';
    });

    it('should fire an event on a helpful vote', done => {
      new AjaxVote(document.querySelector('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect(event.detail.helpful).to.equal('Yes');
        expect(event.detail.url).to.equal('/vote');
        done();
      }
      document.addEventListener('vote', eventListener);
      document.querySelector('input[name="helpful"]').click();
    });

    it('should fire an event on an unhelpful vote', done => {
      new AjaxVote(document.querySelector('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect(event.detail['not-helpful']).to.equal('No');
        expect(event.detail.url).to.equal('/vote');
        done();
      }
      document.addEventListener('vote', eventListener);
      document.querySelector('input[name="not-helpful"]').click();
    });

    it('should include the right data in the request', done => {
      new AjaxVote(document.querySelector('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect(fetchStub.calledOnce).to.equal(true);
        const [url, init] = fetchStub.firstCall.args;
        expect(url).to.equal('/vote');
        expect(init.method).to.equal('POST');
        expect(init.body).to.contain('helpful=Yes');
        done();
      }
      document.addEventListener('vote', eventListener);
      document.querySelector('input[name="helpful"]').click();
    });

    it('should update the UI with the response', done => {
      new AjaxVote(document.querySelector('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      eventListener = function(event) {
        expect(document.querySelector('.ajax-vote-box').textContent)
          .to.equal('Thanks for the vote!');
        done();
      }
      document.addEventListener('vote', eventListener);
      document.querySelector('input[name="helpful"]').click();
    });

  });
});
