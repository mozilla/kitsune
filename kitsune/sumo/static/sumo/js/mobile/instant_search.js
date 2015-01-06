/* globals k:false, jQuery:false */
(function($) {
  function render(data) {
    var context = $.extend({}, data);
    var base_url = k.InstantSearchSettings.searchClient.lastQueryUrl();
    var $searchContent;
    context.base_url = base_url;

    if ($('#instant-search-content').length) {
      $searchContent = $('#instant-search-content');
    } else {
      $searchContent = $('<div />').attr('id', 'instant-search-content').addClass('results wrapper slide-on-exposed');
      $('#main-content').after($searchContent);
    }

    $searchContent.html(k.nunjucksEnv.render('mobile-search-results.html', context));
  }

  window.k.InstantSearchSettings.render = render;

  $(document).on('click', '#search-button', function() {
    var $header = $('body > header');
    var $searchField = $('#instant-search-form input[type="search"]');

    $header.toggleClass('searching');
    if ($header.is('searching')) {
      $searchField.focus();
    } else {
      $searchField.val('');
      $searchField.trigger('keyup'); // Trigger a keyup to simulate the field changing
    }
  });
})(jQuery);
