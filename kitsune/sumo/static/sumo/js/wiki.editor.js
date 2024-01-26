import "@selectize/selectize";

(function($) {
  // Improve the interface for restricting articles.
  $("select[id='id_restrict_to_groups']").selectize({
    placeholder: "No group(s) selected ",
  });
})(jQuery);
