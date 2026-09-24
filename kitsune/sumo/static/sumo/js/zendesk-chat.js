/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { apiFetch } from "sumo/js/utils/fetch";
import { SIGN_OUT_KEY } from "sumo/js/sign-out-sync";

// The ID of the user that last signed-in to the widget.
export const SIGNED_IN_USER_KEY = "zendesk-chat-user";

(function () {
  let html = document.documentElement;
  signInToChat(
    html.getAttribute('data-zendesk-chat-jwt-url'),
    html.getAttribute('data-zendesk-chat-user'),
    html.getAttribute('data-zendesk-chat-tags')
  );
  removeChatOnSignOut();
})();

export function signInToChat(jwtUrl, sessionUser, tags) {
  if (!jwtUrl || !sessionUser || typeof window.zE !== 'function') {
    return;
  }

  let signedIn = window.localStorage.getItem(SIGNED_IN_USER_KEY);

  if (signedIn !== sessionUser) {
    window.zE('messenger', 'logoutUser');
    window.localStorage.removeItem(SIGNED_IN_USER_KEY);
  }

  // After the logout above, which clears them.
  if (tags) {
    window.zE('messenger:set', 'conversationTags', tags.split(' '));
  }

  // Zendesk holds on to this and runs it again whenever it needs a fresh token,
  // for example when the user sends something after the old one expired.
  function fetchToken(callback) {
    apiFetch(jwtUrl, { method: 'POST', dataType: 'text' })
      .then(callback)
      .catch((error) => {
        // We always remove the chat widget, otherwise the user could chat anonymously.
        removeChat();
        // An error means that the user has been refused access to chat (401, 403, 404),
        // rate-limited (429), or another, unexpected error has occurred. We want to show
        // the error in the console for every case other than refusal.
        if (![401, 403, 404].includes(error.response?.status)) {
          console.error('Could not get a Zendesk chat token.', error);
        }
      });
  }

  // Login the user on every page load. The widget doesn't restore an authenticated session
  // on its own, so skipping this leaves the user anonymous with a fresh, empty conversation.
  window.zE('messenger', 'loginUser', fetchToken, (error) => {
    if (error) {
      removeChat();
      console.error('Zendesk chat login failed.', error);
      return;
    }
    window.localStorage.setItem(SIGNED_IN_USER_KEY, sessionUser);
  });
}

export function removeChat() {
  window.zE('messenger', 'logoutUser');
  window.zE('messenger', 'resetWidget');
  window.zE('messenger', 'hide');
}

export function removeChatOnSignOut() {
  if (typeof window.zE !== 'function') {
    return () => {};
  }

  // This tab. Storage events never reach the tab that made the change, so a lone
  // tab would otherwise hear nothing.
  for (const form of document.querySelectorAll('form#sign-out')) {
    form.addEventListener('submit', removeChat);
  }

  // Any other tab.
  function onStorage(event) {
    if (event.key === SIGN_OUT_KEY && event.newValue) {
      removeChat();
    }
  }

  window.addEventListener('storage', onStorage);

  return () => window.removeEventListener('storage', onStorage);
}
