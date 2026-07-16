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

function errorResponse() {
  // A 500 whose body is an HTML error page (as Django serves), which is exactly
  // the case fetch resolves successfully but $.ajax routed to error().
  return {
    ok: false,
    status: 500,
    headers: { get: () => "text/html" },
    json: async () => {
      throw new SyntaxError("Unexpected token <");
    },
    text: async () => "<!doctype html><h1>500</h1>",
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

    it('shows an error and re-enables the buttons when the vote fails', async () => {
      fetchStub.resolves(errorResponse());
      const av = new AjaxVote(document.querySelector('form.vote'), {
        positionMessage: true,
        removeForm: true,
      });
      const yes = document.querySelector('input[name="helpful"]');
      yes.click();

      // Let the rejected apiFetch settle so the .catch handler runs.
      await new Promise(resolve => setTimeout(resolve, 0));

      const box = document.querySelector('.ajax-vote-box');
      expect(box).to.not.equal(null);
      expect(box.textContent).to.equal('There was an error submitting your vote.');
      expect(yes.disabled).to.equal(false);
      expect(av.voted).to.equal(false);
    });

  });
});
