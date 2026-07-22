import { initRecipientAutocomplete } from "sumo/js/tomselect-autocomplete";

/*
 * messages.autocomplete.js
 * A generic autocomplete widget for both groups and users.
 */

export function renderSuggestion(item, escape) {
  var typeIcon =
    '<img src="' + escape(item.type_icon) + '" alt="icon for ' + escape(item.type) + '">';
  // The "avatar" class is applied for the JS-level fallback in profile-avatars.js
  var avatar = '<img src="' + escape(item.avatar) + '" class="avatar"/>';
  // NOTE: `item.type === 'user'` is a pre-existing case mismatch - the API
  // returns 'User'/'Group', so this display_name branch was already dead and
  // the name-only branch is what actually renders. Preserved as-is.
  var label =
    item.display_name && item.type === "user"
      ? escape(item.display_name) + " [" + escape(item.name) + "]"
      : escape(item.name);
  return (
    '<div class="' + escape(item.type) + '">' +
    typeIcon +
    avatar +
    '<div class="name_search">' + label + "</div>" +
    "</div>"
  );
}

function init() {
  document.querySelectorAll("input.user-autocomplete").forEach(function (input) {
    initRecipientAutocomplete(input, {
      apiUrl: document.body.dataset.messagesApi,
      valueField: "type_and_name",
      // Chip shows the full "User: name" / "Group: name" (matches the old
      // widget, which displayed the token value).
      labelField: "type_and_name",
      renderOption: renderSuggestion,
      submitFormOnAdd: true,
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
