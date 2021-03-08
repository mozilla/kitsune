/* globals k:false, jQuery:false, trackEvent:false */
(function($) {
  var searchTimeout;
  var locale = $('html').attr('lang');
  const searchTitle = "Search | Mozilla Support";

  const localStorageUseV2 = {
    "true": true,
    "false": false,
  }[window.localStorage.getItem("enable_search_v2")];

  // the local storage flag overrides everything else:
  if (
    localStorageUseV2 ??
    ($("body").data("readonly") || window.waffle?.flag_is_active("instant_search_v2"))
  ) {
    var search = new k.Search("/" + locale + "/search/v2/");
  } else {
    var search = new k.Search("/" + locale + "/search");
  }

  var cxhr = new k.CachedXHR();
  var aaq_explore_step = $("#question-search-masthead").length > 0;

  const queries = [];
  let renderedQuery;

  function hideContent() {
    $('#main-content').hide();
    $('#main-content').siblings('aside').hide();
    $('body').addClass('search-results-visible');
    $('.home-search-section .mzp-l-content').removeClass('narrow');
    $('.home-search-section').removeClass('extra-pad-bottom');

    // If applicable, close the mobile search field and move the focus to the main field.
    $(".sumo-nav--mobile-search-form").removeClass("mzp-is-open").attr("aria-expanded", "false");

    if (aaq_explore_step) {
      // in aaq explore step we don't want any search to show the default masthead
      $(".hidden-search-masthead").hide();
      $(".question-masthead").show();
      $(".page-heading--logo").css("display", "block");
    } else {
      $(".hidden-search-masthead").show();
    }
  }

  function showContent() {
    $('body').removeClass('search-results-visible');
    $('.home-search-section').addClass('extra-pad-bottom');
    $('.support-search-main').hide();
    $('#main-content').show();
    $('#main-content').siblings('aside').show();
    $('#instant-search-content').remove();
    $('[data-instant-search="form"] input[name="q"]').each(function () {
      $(this).val("");
    });
    $(".page-heading--intro-text").show();
    $(".home-search-section--content .search-results-heading").remove();
    $('.home-search-section .mzp-l-content').addClass('narrow');
    $('.hidden-search-masthead').hide();
  }

  function render(data) {
    var context = $.extend({}, data);

    let query = context.q;
    if (queries.lastIndexOf(query) < queries.lastIndexOf(renderedQuery)) {
      // this query was sent before the query already rendered, don't render it
      return;
    }
    renderedQuery = query;

    let historyState = {
      query,
      params: search.params
    }
    if (history.state?.query) {
      // if a search is already the latest point in history, replace it
      // to avoid filling history with partial searches
      history.replaceState(historyState, searchTitle, "#search");
    } else {
      history.pushState(historyState, searchTitle, "#search");
    }

    var base_url = search.lastQueryUrl();
    var $searchContent;
    context.base_url = base_url;

    if ($('#instant-search-content').length) {
      $searchContent = $('#instant-search-content');
    } else {
      $searchContent = $('<div />').attr('id', 'instant-search-content');
      $('#main-content').after($searchContent);
    }

    var $searchResults = $(k.nunjucksEnv.render("search-results.html", context));
    if (aaq_explore_step) {
      $searchResults.find('section a').attr('target', '_blank');
    }
    $searchContent.html($searchResults);

    // These two functions are coming from the global scope, but should be proper
    // modules when we replace django-compressor with a FE build process.
    detailsInit(); // fold up sidebar on mobile.
    tabsInit();

    // remove and append search results heading
    $(".page-heading--intro-text").hide();
    $(".home-search-section--content .search-results-heading").remove();
    $(".search-results-heading").appendTo(".home-search-section--content");

    // change aaq link if we're in aaq flow
    if (aaq_explore_step) {
      $("#search-results-aaq-link").attr("href", window.location + "/form");
    }
  }

  window.k.InstantSearchSettings = {
    hideContent: hideContent,
    showContent: showContent,
    render: render,
    searchClient: search
  };

  $(document).on('submit', '[data-instant-search="form"]', function(ev) {
    ev.preventDefault();
    $(this).find('.searchbox').focus();
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

      if (history.state?.query) {
        history.pushState({}, searchTitle, location.href.replace("#search", ""));
      }
    } else if ($this.val() !== search.lastQuery) {
      if (searchTimeout) {
        window.clearTimeout(searchTimeout);
      }

      k.InstantSearchSettings.hideContent();

      $form.find('input').each(function () {
        if ($(this).attr('type') === 'submit') {
          return true;
        }
        if ($(this).attr('type') === 'button') {
          return true;
        }
        if ($(this).attr('name') === 'q') {
          var value = $(this).val();
          // update the values in all search forms which aren't the one the user is typing into
          $('[data-instant-search="form"]').not($form).each(function () {
            $(this).find('input[name="q"]').val(value);
          });
          return true;
        }
        params[$(this).attr('name')] = $(this).val();
      });

      searchTimeout = setTimeout(function () {
        if (search.hasLastQuery) {
          trackEvent('Instant Search', 'Exit Search', search.lastQueryUrl());
        }
        search.setParams(params);
        let query = $this.val();
        queries.push(query);
        search.query(query, k.InstantSearchSettings.render);
        trackEvent('Instant Search', 'Search', search.lastQueryUrl());
      }, 200);
    }

    if (formId === "support-search" || formId === "mobile-search-results") {
      window.scrollTo(0, 0);
    }

    if (aaq_explore_step) {
      $(".question-masthead").find("input[name=q]").focus();
    } else if ($(".hidden-search-masthead").length > 0) {
      $(".hidden-search-masthead").find("input[name=q]").focus();
    } else {
      $("#support-search-masthead").find("input[name=q]").focus();
    }
  });

  $(document).on('click', '[data-instant-search="link"]', function(ev) {
    ev.preventDefault();

    var $this = $(this);

    if (search.hasLastQuery) {
      trackEvent('Instant Search', 'Exit Search', search.queryUrl());
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

    search.query(null, k.InstantSearchSettings.render);
    trackEvent("Instant Search", "Search", search.lastQueryUrl());
  });

  // 'Popular searches' feature
  $(document).on('click', '[data-featured-search]', function(ev) {
    var $mainInput = $('#support-search-masthead input[name=q]');
    var thisLink = $(this).text();
    $('#support-search-masthead input[name=q]').focus().val(thisLink);
    $mainInput.trigger( "keyup" );
    ev.preventDefault();
  });

  $(document).on('click', '[data-mobile-nav-search-button]', function(ev) {
    // If we hijack the layout of the page and the user clicks the button again.
    // assume they want to get rid of the search.
    if ($('.hidden-search-masthead').is(':visible')) {
      window.k.InstantSearchSettings.showContent();
    } else if (aaq_explore_step) {
      // in aaq explore step, we don't want to show the default masthead
      $('#question-search-masthead').find('input[name=q]').focus();
      window.scrollTo(0, 0);
    } else if ($('.hidden-search-masthead').length > 0) {
      $('body').addClass('search-results-visible');
      $('.hidden-search-masthead').show();
      $('.hidden-search-masthead').find('input[name=q]').focus();
      window.scrollTo(0, 0);
    } else {
      // catchall for pages with a searchbox in the masthead
      $('.simple-search-form .searchbox').trigger('keyup').focus();
    }

    ev.preventDefault();
  });

  function loadFromHistory(e) {
    let state = e.type == "popstate" ? e.state : history.state;
    if (state?.query) {
      window.k.InstantSearchSettings.hideContent();
      $('[data-instant-search="form"] input[name="q"]').each(function () {
        $(this).val(state.query);
      });
      search.params = state.params;
      queries.push(state.query);
      search.query(state.query, k.InstantSearchSettings.render);
    } else {
      window.k.InstantSearchSettings.showContent();
    }
  }

  window.addEventListener("popstate", loadFromHistory);
  window.addEventListener("DOMContentLoaded", loadFromHistory);
})(jQuery);
