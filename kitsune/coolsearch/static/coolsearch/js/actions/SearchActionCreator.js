/* globals $:false */

import ResultsActionCreator from './ResultsActionCreator.js';


var SearchActionCreator = {
  runSearch: function (dataType, payload) {
    var apiUrl = `/api/2/coolsearch/search/${dataType}/`;

    // Send an AJAX query to the API.
    $.ajax({
      dataType: 'json',
      url: apiUrl,
      data: payload,
      traditional: true,
      success: function success(results) {
        // When we receive the data, send an action to the Dispatcher to notify
        // that new data has arrived.
        ResultsActionCreator.createResults(results);
      }
    });
  }
};

export default SearchActionCreator;
