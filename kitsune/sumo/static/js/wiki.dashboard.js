/*
 * kb dashboard chart
 */

(function($){

"use strict";

$(document).ready(function() {
  if ($('body').is('.locale-metrics')) {
    // Create the dashboard charts.

    makeWikiMetricGraphs();

    makeVoteGraph($('#kpi-vote'), [
      {
        name: gettext('Article Votes: % Helpful'),
        slug: 'wiki_percent',
        func: k.Graph.fraction('kb_helpful', 'kb_votes'),
        type: 'percent',
        axisGroup: 'percent'
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

function makeWikiMetricGraphs() {
  // Get the data we need, process it and create the graphs.
  var $l10n = $('#localization-metrics');
  var $contributors = $('#active-contributors');

  $.getJSON($l10n.data('url'), function(data) {
    var results = data.results;
    var resultsByDate;
    var contributorsByDate = {};
    var l10nByDate = {};
    var i, l, result;

    for (i = 0, l = results.length; i < l; i++) {
      // Split out the results into two groups for two separate graphs:
      // * active_contributors
      // * percent_localized_all, percent_localized_top20
      if (results[i].code === 'active_contributors') {
        resultsByDate = contributorsByDate;
      } else {
        resultsByDate = l10nByDate;
      }

      // If we don't have an entry for that date, create it.
      result = resultsByDate[results[i].date];
      if (!result) {
        result = {
          date: results[i].date
        };
        resultsByDate[results[i].date] = result;
      }

      // Add the new value.
      result[results[i].code] = results[i].value;
    }

    // Create the graphs.
    makeWikiMetricGraph(
      $l10n,
      [
        {
          name: gettext('All Articles: % Localized'),
          slug: 'active_contributors',
          func: k.Graph.identity('percent_localized_all'),
          axisGroup: 'percent'
        },
        {
          name: gettext('Top 20 Articles: % Localized'),
          slug: 'active_contributors',
          func: k.Graph.identity('percent_localized_top20'),
          axisGroup: 'percent'
        }
      ],
      'mini',
      true,
      _.values(l10nByDate)
    );

    makeWikiMetricGraph(
      $contributors,
      [
        {
          name: gettext('Active Contributors'),
          slug: 'active_contributors',
          func: k.Graph.identity('active_contributors'),
          axisGroup: 'contributors'
        }
      ],
      false,
      false,
      _.values(contributorsByDate)
    );

  });

}


function makeWikiMetricGraph($container, descriptors, legend, bucket, results) {
  new k.Graph($container, {
    data: {
      datums: results,
      seriesSpec: descriptors
    },
    options: {
      legend: legend,
      slider: true,
      bucket: bucket
    },
    graph: {
      width: 600,
      height: 300
    },
  }).render();
}

}(jQuery));
