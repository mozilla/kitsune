import Search from "sumo/js/search_utils";
import TomSelect from "tom-select";

import "sumo/tpl/wiki-related-doc.njk";
import "sumo/tpl/wiki-search-results.njk";
import nunjucksEnv from "sumo/js/nunjucks"; // has to be loaded after templates

document.addEventListener("DOMContentLoaded", function() {
  const locale = document.documentElement.lang;
  const search = new Search(`/${locale}/search`, { w: 1, format: 'json' });

  const relatedDocsList = document.getElementById('related-docs-list');
  const searchInput = document.getElementById('search-related');

  if (!searchInput || !relatedDocsList) {
    return;
  }

  if (document.body.classList.contains('edit_metadata') || document.body.classList.contains('new')) {
    relatedDocsList.style.display = 'none';
  }

  let currentDocId = null;
  const documentForm = document.querySelector('form[data-document-id]');
  if (documentForm) {
    currentDocId = documentForm.dataset.documentId;
  }

  const tomSelect = new TomSelect(searchInput, {
    valueField: 'id',
    labelField: 'title',
    searchField: 'title',
    create: false,
    closeAfterSelect: true,
    maxItems: null, // Allow multiple selections
    plugins: {
      remove_button: {
        title: 'Remove this document'
      }
    },
    load: function(query, callback) {
      if (!query.length) {
        return callback();
      }

      search.query(query, function(data) {
        if (!data || !data.results) {
          return callback();
        }

        const formattedResults = data.results
          .filter(result => result.type === 'document')
          .map(item => {
            let id = item.id;
            if (!id && item.url) {
              const match = item.url.match(/\/(\d+)\//);
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
          .filter(item => !currentDocId || String(item.id) !== String(currentDocId));

        callback(formattedResults);
      });
    },
    onItemAdd: function(value, item) {
      const emptyMessage = relatedDocsList.querySelector('.empty-message');
      if (emptyMessage) {
        emptyMessage.remove();
      }
      // Note: The actual list item is added in render.item
    },
    render: {
      option: function(item, escape) {
        return `<div>${escape(item.title)}</div>`;
      },
      // Renders the selected item in the input field and triggers adding the item visually to the list below.
      item: function(item, escape) {
        const context = {
          name: 'related_documents', // Input field name prefix
          doc: {
            id: item.id,
            title: item.title
          }
        };
        relatedDocsList.insertAdjacentHTML('beforeend', nunjucksEnv.render('wiki-related-doc.njk', context));

        // This div is what TomSelect displays in the input field for the selected item
        return `<div>${escape(item.title)}</div>`;
      },
      no_results: function(data, escape) {
        const noDocsFound = typeof gettext !== 'undefined' ? gettext('No documents found') : 'No documents found';
        return `<div class="no-results">${noDocsFound}</div>`;
      }
    }
  });

  // Process pre-existing selected options (for editing existing documents with related docs)
  const preSelectedOptions = searchInput.querySelectorAll('option[selected]');
  if (preSelectedOptions.length > 0) {

    const emptyMessage = relatedDocsList.querySelector('.empty-message');
    if (emptyMessage) {
      emptyMessage.remove();
    }
    
    preSelectedOptions.forEach(option => {
      const docData = {
        id: option.value,
        title: option.textContent
      };
      
      // Add the option to TomSelect's options and selected items
      tomSelect.addOption(docData);
      tomSelect.addItem(option.value, true); // true = silent, don't trigger events
    });
  }

  tomSelect.on('item_remove', function(value) {
    const itemToRemove = relatedDocsList.querySelector(`[data-pk="${value}"]`);
    if (itemToRemove) {
      itemToRemove.remove();
    }

    // Check if there are any document items left (li elements with data-pk attribute)
    const remainingDocs = relatedDocsList.querySelectorAll('li[data-pk]');
    if (remainingDocs.length === 0) {
      const noRelatedDocs = typeof gettext !== 'undefined' ? gettext('No related documents.') : 'No related documents.';
      relatedDocsList.innerHTML = `<div class="empty-message">${noRelatedDocs}</div>`;
    }
  });
});
