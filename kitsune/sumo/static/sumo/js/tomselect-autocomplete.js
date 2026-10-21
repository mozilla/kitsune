import TomSelect from "tom-select";
import "tom-select/dist/css/tom-select.default.css";

import { apiFetch } from "sumo/js/utils/fetch";

/*
 * Recipient/username autocomplete backed by Tom Select - a vanilla replacement
 * for the vendored jquery.tokeninput widget used by users.autocomplete.js and
 * messages.autocomplete.js.
 *
 * Tom Select is attached to the existing <input type="text"> (rendered by a
 * Django Multi*Field TextInput widget) with delimiter ",", so the input keeps a
 * comma-joined list of `valueField` values on submit - exactly what those form
 * fields expect, and what jquery.tokeninput produced.
 */
export function initRecipientAutocomplete(input, options) {
  if (!input) {
    return null;
  }

  var apiUrl = options.apiUrl;
  var valueField = options.valueField;
  var labelField = options.labelField;
  var renderOption = options.renderOption;
  var submitFormOnAdd = options.submitFormOnAdd;

  // Prefill from the input's current comma-separated value.
  var prefillValues = (input.value || "")
    .split(",")
    .map(function (v) {
      return v.trim();
    })
    .filter(Boolean);

  var tomSelect = new TomSelect(input, {
    valueField: valueField,
    labelField: labelField,
    // The autocomplete endpoints match on username OR display name
    // (users/api.py, messages/api.py) and the payload carries both. Tom Select
    // re-runs its local sifter over the loaded options and keeps only those
    // matching a searchField, so display_name must be searchable too -
    // otherwise a result the server matched purely on display name would be
    // dropped client-side (jquery.tokeninput did not re-filter server results).
    // The autocomplete endpoints match on username OR display name
    // (users/api.py, messages/api.py) and the payload carries both. Tom Select
    // re-runs its local sifter over the loaded options and keeps only those
    // matching a searchField, so display_name must be searchable too -
    // otherwise a result the server matched purely on display name would be
    // dropped client-side (jquery.tokeninput did not re-filter server results).
    searchField: options.searchField || [labelField, "display_name"],
    delimiter: ",",
    persist: false,
    create: false,
    closeAfterSelect: true,
    maxItems: null,
    // Hide the placeholder once something is selected. Tom Select otherwise
    // defaults this to false for multi-select, leaving the placeholder on the
    // input line below the selected pills.
    hidePlaceholder: true,
    plugins: {
      remove_button: {},
      // Shrink the text input to fit its content (min-width 4px) instead of the
      // default 7rem, so it flows inline after the last pill rather than
      // wrapping onto its own empty line below the selected pills.
      input_autogrow: {},
    },
    load: function (query, callback) {
      if (!query.length) {
        callback();
        return;
      }
      apiFetch(apiUrl, { data: { term: query }, dataType: "json" })
        .then(function (items) {
          callback(items || []);
        })
        .catch(function () {
          callback();
        });
    },
    render: {
      option: renderOption,
      no_results: function (data, escape) {
        return '<div class="no-results">' + gettext("No results found") + "</div>";
      },
    },
    onItemAdd: function () {
      // Some forms (wrapped in .single) submit as soon as a recipient is picked.
      if (submitFormOnAdd) {
        var single = input.closest(".single");
        if (single) {
          var form = single.closest("form");
          if (form) {
            form.requestSubmit();
          }
        }
      }
    },
  });

  // Seed the prefilled values as options + selected items (they may not be
  // returned by the API). Second arg `true` = add silently (no change event).
  prefillValues.forEach(function (value) {
    var option = {};
    option[valueField] = value;
    option[labelField] = value;
    tomSelect.addOption(option);
    tomSelect.addItem(value, true);
  });

  return tomSelect;
}
