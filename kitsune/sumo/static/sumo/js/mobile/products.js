(function($) {
  var $body = $('body');
  var locale = $('html').attr('lang');
  var search = k.InstantSearchSettings.searchClient;

  if ($body.is('.product-landing') ||  $body.is('.documents')) {
    k.InstantSearchSettings.hideContent = function() {
      $('#content').hide();
    };

    k.InstantSearchSettings.showContent = function() {
      $('#content').show();
      $('#instant-search-content').remove();
    };

    k.InstantSearchSettings.render = function(data) {
      var context = $.extend({}, data);
      var base_url = '/' + locale + '/search?q=' + search.lastQuery;
      base_url += '&' + search.serializeParams();
      context['base_url'] = base_url;

      if ($('#instant-search-content').length) {
        var $searchContent = $('#instant-search-content');
      } else {
        var $searchContent = $('<div />').attr('id', 'instant-search-content');
        $('#content').after($searchContent);
      }

      $searchContent.html(k.nunjucksEnv.render('mobile-product-search-results.html', context));
    };
  }
})(jQuery);
