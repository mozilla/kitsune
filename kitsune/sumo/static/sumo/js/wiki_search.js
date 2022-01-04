import nunjucksEnv from "sumo/js/nunjucks";
import Search from "sumo/js/search_utils";

(function($) {
  var searchTimeout;
  var locale = $('html').attr('lang');

  var $searchField = $('#search-related');
  var $relatedDocsList = $('#related-docs-list');
  var $resultsList;

  // To search for only wiki articles we pass w=1
  var search = new Search('/' + locale + '/search', {w: 1, format: 'json'});

  function createResultsList() {
    $resultsList = $('<div />').addClass('input-dropdown');
    $searchField.after($resultsList);
    $resultsList.css('width', $searchField.outerWidth());
    $resultsList.show();

    $resultsList.on('click', '[data-pk]', function() {
      var $this = $(this);

      $relatedDocsList.children('.empty-message').remove();

      if (!$relatedDocsList.children('[data-pk=' + $this.data('pk') + ']').length) {
        var context = {
          name: 'related_documents',
          doc: {
            id: $this.data('pk'),
            title: $this.text()
          }
        };

        $relatedDocsList.append(nunjucksEnv.render('wiki-related-doc.html', context));
      }
    });
  }

  function showResults(data) {
    if (!$resultsList) {
      createResultsList();
    }
    $resultsList.html(nunjucksEnv.render('wiki-search-results.html', data));
  }

  function handleSearch() {
    var $this = $(this);
    if ($this.val().length === 0) {
      window.clearTimeout(searchTimeout);
      if ($resultsList) {
        $resultsList.html('');
        $resultsList.hide();
      }
    } else if ($this.val() !== search.lastQuery) {
      window.clearTimeout(searchTimeout);
      searchTimeout = window.setTimeout(function () {
        search.query($this.val(), showResults);
      }, 200);
    }
  }

  $searchField.on('keyup', handleSearch);

  $searchField.on('focus', function() {
    if ($resultsList) {
      $resultsList.show();
    }
  });

  $searchField.on('blur', function() {
    if ($resultsList) {
      // We use a timeout to ensure that you can still click on the dropdown
      window.setTimeout(function() {
        $resultsList.hide();
      }, 100);
    }
  });
})(jQuery);
