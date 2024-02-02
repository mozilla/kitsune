import "@selectize/selectize";

(function($) {
  // Improve the interface for restricting articles.
  $(function () {
    $("select[id='id_restrict_to_groups']").selectize({
      placeholder: "Restrict visibility to selected group(s)   ",
    });
  });
})(jQuery);
