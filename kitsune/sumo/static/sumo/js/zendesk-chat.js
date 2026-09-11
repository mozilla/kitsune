/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { apiFetch } from "sumo/js/utils/fetch";

// Who we last signed in to the widget, so we can tell when a different user takes
// over the browser. We keep our own record because the messaging API can't be asked
// - it has no status call and no login event. Local storage because that's where the
// widget keeps its own session: shared across tabs, and surviving a browser close.
export const STORAGE_KEY = "zendesk-chat-user";

(function () {
  let html = document.documentElement;
  signInToChat(
    html.getAttribute('data-zendesk-chat-jwt-url'),
    html.getAttribute('data-zendesk-chat-user')
  );
})();

export function signInToChat(jwtUrl, sessionUser) {
  if (!jwtUrl || !sessionUser || typeof window.zE !== 'function') {
    return;
  }

  let signedIn = window.localStorage.getItem(STORAGE_KEY);

  if (signedIn && signedIn !== sessionUser) {
    // Clear the previous user out. loginUser on its own doesn't replace them -
    // tested on dev, where the new user saw the old one's conversation. logoutUser
    // takes no callback, so this relies on zE running queued commands in order.
    window.zE('messenger', 'logoutUser');
    window.localStorage.removeItem(STORAGE_KEY);
  }

  // Zendesk holds on to this and runs it again whenever it needs a fresh token,
  // so it has to hit the network every time rather than reuse one.
  function fetchToken(callback) {
    apiFetch(jwtUrl, { method: 'POST', dataType: 'text' })
      .then(callback)
      .catch((error) => {
        console.error('Could not get a Zendesk chat token.', error);
      });
  }

  // Every page load, not just when the user changes: the widget doesn't restore an
  // authenticated session on its own, so skipping this leaves the visitor anonymous
  // with a fresh, empty conversation.
  window.zE('messenger', 'loginUser', fetchToken, (error) => {
    if (error) {
      console.error('Zendesk chat login failed.', error);
      return;
    }
    window.localStorage.setItem(STORAGE_KEY, sessionUser);
  });
}
