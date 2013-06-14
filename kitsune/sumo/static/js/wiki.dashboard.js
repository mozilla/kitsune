/*
 * kb dashboard chart
 */

(function($){

"use strict";

$(document).ready(function() {
  if ($('body').is('.contributor-dashboard, .localization-dashboard')) {
    // Create the dashboard chart.
    makeVoteGraph($('#kpi-vote'), [
      {
        'name': gettext('Article Votes: % Helpful'),
        'slug': 'wiki_percent',
        'func': k.Graph.fraction('kb_helpful', 'kb_votes'),
        'percent': percent
      }
    ]);
  }

  // product selector page reloading
  $('#product-selector select').change(function() {
    var val = $(this).val();
    var queryParams = k.getQueryParamsAsDict(document.location.toString());

    if (val === '') {
      delete queryParams['product'];
    } else {
      queryParams['product'] = val;
    }
    document.location = document.location.pathname + '?' + $.param(queryParams);
  });
});

function makeVoteGraph($container, descriptors) {
  $.getJSON($container.data('url'), function(data) {
    new k.Graph($container, {
      data: {
        datums: data.objects,
        seriesSpec: descriptors
      },
      options: {
        legend: false,
        slider: true,
        bucket: true
      },
      graph: {
        width: 600,
        height: 300
      },
    }).render();
  });
}

}(jQuery));
