;(function($) {
  "use strict";
  $(document).ready(function() {
    $('.sidebar-folding > li > a').click(function() {
      $(this).parent().toggleClass('selected');
      return false;
    });

    $('.close-button').click(function() {
      var $this = $(this);
      if ($this.data('close-id')) {
        $('#' + $this.data('close-id')).hide();
      } else {
        $this.parent().hide();
      }
    });
  });
})(jQuery);