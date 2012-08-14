;(function($) {
  $(document).ready(function() {
    $('.sidebar-folding > li').click(function() {
      $(this).toggleClass('selected');
      return false;
    });
  });
})(jQuery);