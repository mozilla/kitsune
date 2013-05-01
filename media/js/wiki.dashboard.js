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
        'func': k.Graph.fraction('kb_helpful', 'kb_votes')
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


// TODO: The next two functions are copied from the kpi dasbhoard script
// The only change is the width. We should roll this up into rickshaw_utils
// maybe?

// parseInt and _.map don't get along because parseInt takes a second arg.
// This doesn't have that problem.
function parseNum(n) {
  return parseInt(n, 10);
}

function makeVoteGraph($container, descriptors, metadata) {
  $.getJSON($container.data('url'), function(data) {
    var date, series, graph, split;

    $.each(data.objects, function(d) {
      date = this.date || this.created || this.start;
      // Assume something like 2013-12-31
      split = _.map(date.split('-'), parseNum);
      // The Data constructor takes months as 0 through 11. Wtf.
      this.date = +new Date(split[0], split[1] - 1, split[2]) / 1000;
      this.start = undefined;
      this.created = undefined;
    });

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
      metadata: metadata
    }).render();
  });
}

}(jQuery));
