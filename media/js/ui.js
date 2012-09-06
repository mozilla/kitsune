;(function($) {
  "use strict";
  $(document).ready(function() {
    $('.sidebar-folding > li > a, .sidebar-folding > li > span').click(function() {
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

    $('.btn, a').each(function() {
      var $this = $(this);
      var $form = $this.closest('form');

      if ($this.attr('data-type') === 'submit') {
        if ($this.attr('data-form')) {
          $form = $('#' + $this.attr('data-form'));
        }

        $this.on('click', function() {
          var name = $this.attr('data-name');
          var value = $this.attr('data-value');

          if (name) {
            var $input = $('<input type="hidden">');

            $input.attr('name', name);

            if (value) {
              $input.val(value);
            } else {
              $input.val('1');
            }

            $form.append($input);
          }

          if ($this.attr('data-nosubmit') !== '1') {
            $form.trigger('submit');
          }
        });
      }
    });

    $('.folding-section, [data-ui-type="folding-section"]').each(function() {
      var $this = $(this);
      $this.children('header').on('click', function() {
        $this.toggleClass('collapsed');
      });
    });
  });
})(jQuery);