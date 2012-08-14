;(function($) {
  $(document).ready(function() {
    $('.sidebar-folding > li > a').click(function() {
      $(this).parent().toggleClass('selected');
      return false;
    });
  });
})(jQuery);