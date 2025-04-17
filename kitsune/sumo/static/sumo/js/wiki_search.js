import Search from "sumo/js/search_utils";
import TomSelect from "tom-select";

import "sumo/tpl/wiki-related-doc.njk";
import "sumo/tpl/wiki-search-results.njk";
import nunjucksEnv from "sumo/js/nunjucks"; // has to be loaded after templates

(function($) {
  var locale = $('html').attr('lang');
  var search = new Search('/' + locale + '/search', {w: 1, format: 'json'});

  document.addEventListener("DOMContentLoaded", function() {
    var $relatedDocsList = $('#related-docs-list');
    var searchInput = document.getElementById('search-related');
    
    if (!searchInput) return;

    if (document.body.classList.contains('edit_metadata') || document.body.classList.contains('new')) {
      $relatedDocsList.css('display', 'none');
    }

    var currentDocId = null;
    var $documentForm = $('form[data-document-id]');
    if ($documentForm.length) {
      currentDocId = $documentForm.data('document-id');
    }

    var tomSelect = new TomSelect(searchInput, {
      valueField: 'id',
      labelField: 'title',
      searchField: 'title',
      create: false,
      closeAfterSelect: true,
      maxItems: null,
      plugins: {
        remove_button: {
          title: 'Remove this document'
        }
      },
      load: function(query, callback) {
        if (!query.length) return callback();
        
        search.query(query, function(data) {
          if (!data || !data.results) {
            return callback();
          }
          
          var formattedResults = data.results
            .filter(result => result.type === 'document')
            .map(function(item) {
              var id = item.id;
              if (!id && item.url) {
                var match = item.url.match(/\/(\d+)\//);
                if (match) {
                  id = match[1];
                }
              }
              
              return {
                id: id,
                title: item.title,
                url: item.url
              };
            })
            .filter(item => item.id)
            .filter(item => !currentDocId || item.id != currentDocId)
          callback(formattedResults);
        });
      },
      onItemAdd: function(value, item) {
        $relatedDocsList.children('.empty-message').remove();
      },
      render: {
        option: function(item, escape) {
          return '<div>' + escape(item.title) + '</div>';
        },
        item: function(item, escape) {
          var context = {
            name: 'related_documents',
            doc: {
              id: item.id,
              title: item.title
            }
          };
          
          $relatedDocsList.append(nunjucksEnv.render('wiki-related-doc.njk', context));
          
          return '<div>' + escape(item.title) + '</div>';
        },
        no_results: function(data, escape) {
          return '<div class="no-results">No documents found</div>';
        }
      }
    });
    
    tomSelect.on('item_remove', function(value) {
      $relatedDocsList.children('[data-pk=' + value + ']').remove();
      
      if (!$relatedDocsList.children().length) {
        $relatedDocsList.html('<div class="empty-message">' + gettext('No related documents.') + '</div>');
      }
    });
  });
})(jQuery);
