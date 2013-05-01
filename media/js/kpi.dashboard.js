(function() {

"use strict";

function init() {
  window.App = new KpiDashboard({
    el: document.getElementById('kpi-dash-app')
  });

  makeKPIGraph($('#kpi-vote'), [
    {
      'name': gettext('Article Votes: % Helpful'),
      'slug': 'wiki_percent',
      'func': k.Graph.fraction('kb_helpful', 'kb_votes')
    },
    {
      'name': gettext('Answer Votes: % Helpful'),
      'slug': 'ans_percent',
      'func': k.Graph.fraction('ans_helpful', 'ans_votes')
    }
  ]);

  makeKPIGraph($('#kpi-active-contributors'), [
    {
      name: gettext('en-US KB'),
      slug: 'en_us',
      func: k.Graph.identity('en_us')
    },
    {
      name: gettext('non en-US KB'),
      slug: 'non_en_us',
      func: k.Graph.identity('non_en_us')
    },
    {
      name: gettext('Support Forum'),
      slug: 'support_forum',
      func: k.Graph.identity('support_forum')
    },
    {
      name: gettext('Army of Awesome'),
      slug: 'aoa',
      func: k.Graph.identity('aoa')
    }
  ]);

  makeKPIGraph($('#kpi-ctr'), [
    {
      name: gettext('CTR %'),
      slug: 'ctr',
      func: k.Graph.fraction('clicks', 'searches')
    }
  ]);

  makeKPIGraph($('#kpi-visitors'), [
    {
      name: gettext('Visitors'),
      slug: 'visitors',
      func: k.Graph.identity('visitors')
    }
  ]);

  makeKPIGraph($('#kpi-l10n'), [
    {
      name: gettext('L10n Coverage'),
      slug: 'l10n',
      // the api returns 0 to 100, we want 0.0 to 1.0.
      func: function(d) { return d['coverage'] / 100; }
    }
  ]);

}

// parseInt and _.map don't get along because parseInt takes a second arg.
// This doesn't have that problem.
function parseNum(n) {
  return parseInt(n, 10);
}

function makeKPIGraph($container, descriptors, metadata) {
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
        width: 880,
        height: 300
      },
      metadata: metadata
    }).render();
  });
}

// Backbone View for the questions chart.

window.KpiDashboard = Backbone.View.extend({
  initialize: function() {
    // Create the models.
    this.questionsChart = new ChartModel([], {
      url: $(this.el).data('questions-url')
    });

    // Create the views.
    this.questionsView = new StockChartView({
      model: this.questionsChart,
      title: gettext('Questions'),
      percent: true,
      series: [{
        name: gettext('Questions'),
        type: 'area',
        yAxis: 1,
        approximation: 'sum',
        mapper: function(o) {
          return {
            x: Date.parse(o['date']),
            y: o['questions']
          };
        }
      }, {
        name: gettext('Solved'),
        numerator: 'solved',
        denominator: 'questions',
        tooltip: {
          ySuffix: '%',
          yDecimals: 1
        }
      }, {
        name: gettext('Responded in 24 hours'),
        numerator: 'responded_24',
        denominator: 'questions',
        tooltip: {
          ySuffix: '%',
          yDecimals: 1
        }
      }, {
        name: gettext('Responded in 72 hours'),
        numerator: 'responded_72',
        denominator: 'questions',
        tooltip: {
          ySuffix: '%',
          yDecimals: 1
        }
      }]
    });

    // Render the view.
    $(this.el)
      .prepend($('#kpi-legend-questions'))
      .prepend(this.questionsView.render().el);

    // Load up the model.
    this.questionsChart.fetch();
  }
});

$(init);

})();