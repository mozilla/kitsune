/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// The purpose of this code is to announce a sign-out to any other interested tabs.
// We use local storage because its change events will reach all tabs other than the
// one that made the change, and because the write completes even if the tab that
// made the change is closing.
export const SIGN_OUT_KEY = "sumo-signed-out";

(function () {
  announceSignOutToOtherTabs();
})();

export function announceSignOutToOtherTabs() {
  // The profile page renders a second sign-out form, sharing the id. Submit fires
  // because ui.js submits with requestSubmit.
  for (const form of document.querySelectorAll('form#sign-out')) {
    form.addEventListener('submit', () => {
      // A fresh value each time, so a later sign-out still reads as a change.
      window.localStorage.setItem(SIGN_OUT_KEY, Date.now());
    });
  }
}
