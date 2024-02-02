import "@selectize/selectize";

(function($) {
  // Improve the interface for restricting articles.
  $(function () {
    $("select[id='id_restrict_to_groups']").selectize({
      closeAfterSelect: true,
      plugins: ["clear_button", "remove_button"],
      placeholder: "Restrict visibility to selected group(s)   ",
    });
  });
})(jQuery);
