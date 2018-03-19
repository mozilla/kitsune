/* globals k:false, jQuery:false, trackEvent:false, trackPageview:false */
(function($) {
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
    var base_url = search.lastQueryUrl();
    var $searchContent;
    context.base_url = base_url;

    if ($('#instant-search-content').length) {
      $searchContent = $('#instant-search-content');
    } else {
      $searchContent = $('<div />').attr('id', 'instant-search-content');
      $('#main-content').after($searchContent);
    }

    $searchContent.html(k.nunjucksEnv.render('search-results.html', context));
  }

  window.k.InstantSearchSettings = {
    hideContent: hideContent,
    showContent: showContent,
    render: render,
    searchClient: search
  };

  $(document).on('submit', '[data-instant-search="form"]', function(ev) {
    ev.preventDefault();
  });

  $(document).on('keyup', '[data-instant-search="form"] input[type="search"]', function(ev) {
    var $this = $(this);
    var params = {
      format: 'json'
    };

    if ($this.val().length === 0) {
      if (searchTimeout) {
        window.clearTimeout(searchTimeout);
      }

      window.k.InstantSearchSettings.showContent();
    } else if ($this.val() !== search.lastQuery) {
      if (searchTimeout) {
        window.clearTimeout(searchTimeout);
      }

      $this.closest('form').find('input').each(function () {
        if ($(this).attr('type') === 'submit') {
          return true;
        }
        if ($(this).attr('type') === 'button') {
          return true;
        }
        if ($(this).attr('name') === 'q') {
          return true;
        }
        params[$(this).attr('name')] = $(this).val();
      });

      searchTimeout = setTimeout(function () {
        if (search.hasLastQuery) {
          trackEvent('Instant Search', 'Exit Search', search.lastQueryUrl());
        }
        search.setParams(params);
        search.query($this.val(), k.InstantSearchSettings.render);
        trackEvent('Instant Search', 'Search', search.lastQueryUrl());
        trackPageview(search.lastQueryUrl());
      }, 200);

      k.InstantSearchSettings.hideContent();
    }
  });

  $(document).on('click', '[data-instant-search="link"]', function(ev) {
    ev.preventDefault();

    var $this = $(this);

    if (search.hasLastQuery) {
      trackEvent('Instant Search', 'Exit Search', search.queryUrl(search.lastQuery));
    }

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

    trackEvent('Instant Search', 'Search', $this.data('href'));
    trackPageview($this.data('href'));

    cxhr.request($this.data('href'), {
      data: {format: 'json'},
      dataType: 'json',
      success: k.InstantSearchSettings.render
    });
  });
})(jQuery);
