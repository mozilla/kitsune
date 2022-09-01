import "jquery-ui/ui/widgets/tabs";

$(function() {
  // initiate tabs
  var tabs = $('#search-tabs').tabs(),
    cache_search_date = $('.showhide-input');

  $('#tab-wrapper form').on("submit", function() {
    $('input.auto-fill').each(function() {
      if ($(this).val() === $(this).attr('placeholder')) {
        $(this).val('');
      }
    });
  });

  $('select', cache_search_date).trigger(function () {
    if ($(this).val() === 0) {
      $('input', $(this).parent()).hide();
    } else {
      $('input', $(this).parent()).show();
    }
  }).trigger();

  switch (parseInt($('#where').text(), 10)) {
    case 4:
      tabs.tabs({active: 2});
      break;
    case 2:
      tabs.tabs({active: 1});
      break;
    case 1:
    default:
      tabs.tabs({active: 0});
  }
});
