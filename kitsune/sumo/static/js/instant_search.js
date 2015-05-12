(function($, _) {
  var searchTimeout;
  var locale = $('html').attr('lang');

  var search = new k.Search('/' + locale + '/search');
  var cxhr = new k.CachedXHR();

  function hideContent() {
    $('#main-content').hide();
    $('#main-content').siblings('aside').hide();
    $('#main-breadcrumbs').hide();
  }

  function showContent() {
    $('#main-content').show();
    $('#main-content').siblings('aside').show();
    $('#main-breadcrumbs').show();
    $('#instant-search-content').remove();
  }

  function render(data) {
    var context = $.extend({}, data);
    var base_url = '/' + locale + '/search?q=' + search.lastQuery;
    base_url += '&' + search.serializeParams();
    context['base_url'] = base_url;

    if ($('#instant-search-content').length) {
      var $searchContent = $('#instant-search-content');
    } else {
      var $searchContent = $('<div />').attr('id', 'instant-search-content');
      $('#main-content').after($searchContent);
    }

    $searchContent.html(_.render('search-results.html', context));
  }

  $(document).on('submit', '[data-instant-search="form"]', function(ev) {
    ev.preventDefault();
  });

  $(document).on('keyup', '[data-instant-search="form"] input[type="search"]', function(ev) {
    var $this = $(this);
    var params = {
      format: 'json'
    }

    if ($this.val().length === 0) {
      if (searchTimeout) {
        window.clearTimeout(searchTimeout);
      }

      showContent();
    } else if ($this.val() !== search.lastQuery) {
      if (searchTimeout) {
        window.clearTimeout(searchTimeout);
      }

      $this.closest('form').find('input').each(function () {
        if ($(this).attr('type') === 'submit') return true;
        if ($(this).attr('type') === 'button') return true;
        if ($(this).attr('name') === 'q')  return true;
        params[$(this).attr('name')] = $(this).val();
      });

      searchTimeout = setTimeout(function () {
        search.setParams(params);
        search.query($this.val(), render);
      }, 200);

      hideContent();
    }
  });

  $(document).on('click', '[data-instant-search="link"]', function(ev) {
    ev.preventDefault();

    var $this = $(this);

    var setParams = $this.data('instant-search-set-params');
    if (setParams) {
      setParams = setParams.split('&');
      $(setParams).each(function() {
        var p = this.split('=');
        search.setParam(p.shift(), p.join('='));
      });
    }

    var unsetParams = $this.data('instant-search-unset-params');
    if (unsetParams) {
      unsetParams = unsetParams.split('&');
      $(unsetParams).each(function() {
        search.unsetParam(this);
      });
    }

    cxhr.request($this.data('href'), {
      data: {format: 'json'},
      dataType: 'json',
      success: render
    });
  });
})(jQuery, k.nunjucksEnv);
