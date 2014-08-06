(function($, _) {
  var searchTimeout;
  var lastInstantSearch;

  var locale = $('html').attr('lang');

  function search(data) {
    var cb = function (data) {
      lastInstantSearch = data['q'];
      var esab = $('input[name="esab"]').val();
      if ($('#instant-search-content').length) {
        var $searchContent = $('#instant-search-content');
      } else {
        var $searchContent = $('<div />').attr('id', 'instant-search-content');
      }
      $('#main-content').after($searchContent);
      var ctx = $.extend({}, data);

      var base_url = '/' + locale + '/search?q=' + data['q'];
      if (esab) {
        base_url += '&esab=' + esab;
        ctx['esab'] = esab;
      }
      ctx['base_url'] = base_url;

      $searchContent.html(_.render('search-results.html', ctx));
    };

    if (typeof data === 'string') {
      $.get(data, {}, cb, 'json');
    } else {
      $.get('/' + locale + '/search', data, cb, 'json');
    }
  }

  $(document).on('keyup', 'input[type="search"]', function() {
    var $this = $(this);

    if ($this.val().length === 0) {
      if (searchTimeout) {
        window.clearTimeout(searchTimeout);
      }
      lastInstantSearch = '';
      $('#main-content').show();
      $('#main-breadcrumbs').show();
      $('#instant-search-content').remove();
    } else {
      if ($this.val() !== lastInstantSearch) {
        if (searchTimeout) {
          window.clearTimeout(searchTimeout);
        }

        var esab = $(this).closest('input[name="esab"]').val();

        searchTimeout = setTimeout(function () {
          var data = {
            'format': 'json',
            'q': $this.val()
          };

          if (esab) {
            data['esab'] = esab;
          }

          $('#main-content').hide();
          $('#main-breadcrumbs').hide();

          search(data);
        }, 100);
      }
    }
  });

  $(document).on('click', '[data-instant-search]', function(ev) {
    ev.preventDefault();
    var $this = $(this);
    if ($this.data('instant-search') === 'link') {
      search($this.data('href'));
    }
  });
})(jQuery, k.nunjucksEnv);
