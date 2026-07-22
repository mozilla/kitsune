import { initRecipientAutocomplete } from "sumo/js/tomselect-autocomplete";

/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */

export function renderUserOption(item, escape) {
  // The "avatar" class is applied for the JS-level fallback in profile-avatars.js
  var avatar = '<img src="' + escape(item.avatar) + '" class="avatar"/>';
  var label = item.display_name
    ? escape(item.display_name) + " [" + escape(item.username) + "]"
    : escape(item.username);
  return "<div>" + avatar + '<div class="name_search">' + label + "</div></div>";
}

function init() {
  document.querySelectorAll("input.user-autocomplete").forEach(function (input) {
    initRecipientAutocomplete(input, {
      apiUrl: document.body.dataset.usernamesApi,
      valueField: "username",
      labelField: "username",
      renderOption: renderUserOption,
      submitFormOnAdd: true,
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
