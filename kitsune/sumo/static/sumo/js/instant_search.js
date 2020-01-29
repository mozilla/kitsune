/* globals k:false, jQuery:false, trackEvent:false */
(function($) {
  var searchTimeout;
  var locale = $('html').attr('lang');

  var search = new k.Search('/' + locale + '/search');
  var cxhr = new k.CachedXHR();

  function hideContent() {
    $('#main-content').hide();
    $('#main-content').siblings('aside').hide();
    $('body').addClass('search-results-visible');
    $('.home-search-section .mzp-l-content').removeClass('narrow');

    // clear sidebar form and focus if is's there.
    $('#support-search-wiki').find('input[name=q]').val('');
  }

  function showContent() {
    $('body').removeClass('search-results-visible');
    $('.support-search-main').hide();
    $('#main-content').show();
    $('#main-content').siblings('aside').show();
    $('#instant-search-content').remove();
    $('.search-form-large:visible').find('input[name=q]').focus().val('');
    $('#support-search').find('input[name=q]').val('');
    $(".home-search-section--content .search-results-heading").remove();
    $('.home-search-section .mzp-l-content').addClass('narrow');

    // move form back to sidebar if in the document.html template.
    if ($('#support-search-wiki:visible').length > 0) {
      $('.hidden-search-masthead').hide();
      // $('#support-search-wiki').appendTo('.search-form-sidebar')
    }
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

    // These two functions are coming from the global scope, but should be proper
    // modules when we replace django-compressor with a FE build process.
    detailsInit(); // fold up sidebar on mobile.
    tabsInit();

    // remove and append search results heading
    $(".home-search-section--content .search-results-heading").remove();
    $(".search-results-heading").appendTo(".home-search-section--content");
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
    var $form = $this.closest('form');
    var formId = $form.attr('id');
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

      $form.find('input').each(function () {
        if ($(this).attr('type') === 'submit') {
          return true;
        }
        if ($(this).attr('type') === 'button') {
          return true;
        }
        if ($(this).attr('name') === 'q') {
          var value = $(this).val();

          if (formId === 'support-search-results') {
            $('#support-search').find('input[name=q]').val(value);
          } else if (formId === 'support-search') {
            $('.hidden-search-masthead').show();
            $('.hidden-search-masthead').find('input[name=q]').val(value).focus();
            // $form.appendTo(".search-form-placeholder");
            window.scrollTo(0, 0);

          } else if (formId === 'support-search-wiki') {
            $('.hidden-search-masthead').show();
            $('.hidden-search-masthead').find('input[name=q]').val(value).focus();
            // $form.appendTo(".search-form-placeholder");
          } else {
            $('#support-search').find('input[name=q]').val(value);
            $('#support-search-results').find('input[name=q]').val(value).focus();
          }

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

    cxhr.request($this.data('href'), {
      data: {format: 'json'},
      dataType: 'json',
      success: k.InstantSearchSettings.render
    });
  });

  // 'Popular searches' feature
  $(document).on('click', '[data-featured-search]', function(ev) {
    var $mainInput = $('#support-search-masthead input[name=q]');
    var thisLink = $(this).text();
    $('#support-search-masthead input[name=q]').focus().val(thisLink);
    $mainInput.trigger( "keyup" );
    ev.preventDefault();
  });
})(jQuery);
