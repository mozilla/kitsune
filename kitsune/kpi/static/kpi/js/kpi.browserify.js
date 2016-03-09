/* globals $:false, gettext: false, k: false, _: false, d3: false, moment: false */
import Chart from './components/Chart.es6.js';

let chartSetups = {
  'retention': {
    'options': {
      axes: {
        xAxis: {
          labels() {
            let labelsArray = [];
            _.each(_.range(1, 13), function(val) {
              labelsArray.push(gettext('Week') + ' ' + val);
            });
            return labelsArray;
          }
        }
      }
    }
  },
  'csat': {
    'bucket': true,
    'descriptors': [
      {
        name: gettext('Average Satisfaction'),
        slug: 'csat',
        func(d) { return d.csat / 100; },
        type: 'percent'
      }
    ]
  },
  'questions': {
    'bucket': true,
    'descriptors': [
      {
        name: gettext('Questions'),
        slug: 'questions',
        func: k.Graph.identity('questions'),
        color: '#5d84b2',
        axisGroup: 'questions',
        area: true
      },
      {
        name: gettext('Solved'),
        slug: 'num_solved',
        func: k.Graph.identity('solved'),
        color: '#aa4643',
        axisGroup: 'questions',
        area: true
      },
      {
        name: gettext('% Solved'),
        slug: 'solved',
        func: k.Graph.fraction('solved', 'questions'),
        color: '#aa4643',
        axisGroup: 'percent',
        type: 'percent'
      },
      {
        name: gettext('Responded in 24 hours'),
        slug: 'num_responded_24',
        func: k.Graph.identity('responded_24'),
        color: '#89a54e',
        axisGroup: 'questions',
        area: true
      },
      {
        name: gettext('% Responded in 24 hours'),
        slug: 'responded_24',
        func: k.Graph.fraction('responded_24', 'questions'),
        color: '#89a54e',
        axisGroup: 'percent',
        type: 'percent'
      },
      {
        name: gettext('Responded in 72 hours'),
        slug: 'num_responded_72',
        func: k.Graph.identity('responded_72'),
        color: '#80699b',
        axisGroup: 'questions',
        area: true
      },
      {
        name: gettext('% Responded in 72 hours'),
        slug: 'responded_72',
        func: k.Graph.fraction('responded_72', 'questions'),
        color: '#80699b',
        axisGroup: 'percent',
        type: 'percent'
      },
      {
        name: gettext('Not responded in 24 hours'),
        slug: 'not_responded_24',
        color: '#C98531',
        func: k.Graph.difference('questions', 'responded_24'),
        area: true
      },
      {
        name: gettext('Not responded in 72 hours'),
        slug: 'not_responded_72',
        color: '#DB75C2',
        func: k.Graph.difference('questions', 'responded_72'),
        area: true
      }
    ]
  },
  'vote': {
    'bucket': true,
    'descriptors': [
      {
        name: gettext('Article Votes: % Helpful'),
        slug: 'wiki_percent',
        func: k.Graph.fraction('kb_helpful', 'kb_votes'),
        type: 'percent'
      },
      {
        name: gettext('Answer Votes: % Helpful'),
        slug: 'ans_percent',
        func: k.Graph.fraction('ans_helpful', 'ans_votes'),
        type: 'percent'
      }
    ]
  },
  'activeContributors': {
    'bucket': false,
    'descriptors': [
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
    ]
  },
  'ctr': {
    'bucket': true,
    'descriptors': [
      {
        name: gettext('Click Through Rate %'),
        slug: 'ctr',
        func: k.Graph.fraction('clicks', 'searches'),
        type: 'percent'
      }
    ]
  },
  'visitors': {
    'bucket': true,
    'descriptors': [
      {
        name: gettext('Visitors'),
        slug: 'visitors',
        func: k.Graph.identity('visitors')
      }
    ]
  },
  'l10n': {
    'container': $('#kpi-l10n'),
    'bucket': true,
    'descriptors': [
      {
        name: gettext('L10n Coverage'),
        slug: 'l10n',
        // the api returns 0 to 100, we want 0.0 to 1.0.
        func(d) { return d.coverage / 100; },
        type: 'percent'
      }
    ]
  },
  'exitSurvey': {
    'bucket': true,
    'descriptors': [
      {
        name: gettext('Percent Yes'),
        slug: 'percent_yes',
        func: k.Graph.percentage('yes', 'no', 'dont_know'),
        axisGroup: 'percent',
        type: 'percent'
      },
      {
        name: gettext('Yes'),
        slug: 'yes',
        func: k.Graph.identity('yes'),
        axisGroup: 'response'
      },
      {
        name: gettext('No'),
        slug: 'no',
        func: k.Graph.identity('no'),
        axisGroup: 'response'
      },
      {
        name: gettext("I don't know"),
        slug: 'dont_know',
        func: k.Graph.identity('dont_know'),
        axisGroup: 'response'
      }
    ]
  }
};

$('.graph').each(function() {
  let $graphElem = $(this);
  let chartType = $graphElem.data('chart-type');
  let chartSlug = $graphElem.data('slug');
  let chartSettings = chartSetups[chartSlug];
  chartSettings.container = $graphElem.closest('section');

  (chartType === 'd3') ? makeRetentionChart(chartSettings) : makeKPIGraph(chartSettings);
})

function getChartData(url, propertyKey) {
  let dataReady = $.Deferred();
  let datumsToCollect = propertyKey;
  let fetchData = (url, existingData) => {
    $.getJSON(url, function(data) {
      existingData = existingData.concat(data[datumsToCollect] || data);
      if (data.next) {
        return fetchData(data.next, existingData);
      } else {
        dataReady.resolve(existingData);
      }
    }).fail(function(error) {
      dataReady.reject(error);
    });
  }

  fetchData(url, []);
  return dataReady;
}

function handleDataError($container) {
  let errorMsg = document.createElement('p');
  $(errorMsg).text(gettext('Error loading graph')).addClass('error');
  $container.empty().append(errorMsg);
}

function makeRetentionChart(settings) {
  let $container = settings.container;
  let startDate = moment().day(1).day(-84).format('YYYY-MM-DD');
  let defaultContributorType = $container.data('contributor-type') || 'contributor';
  let urlToFetch = `${$container.data('url')}?start=${startDate}`;
  let fetchDataset = getChartData(urlToFetch, 'results');
  let retentionChart = new Chart($container, settings.options);
  let $errorContainer = $container.children('div');

  fetchDataset.done(data => {
    retentionChart.data = data;
    retentionChart.axes.yAxis.labels = _.uniq(_.pluck(data, 'start'));
    retentionChart.setupAxis('yAxis');
    retentionChart.populateData(defaultContributorType);

    $('#toggle-cohort-type').change(function() {
      let cohortType = $(this).val();
      retentionChart.populateData(cohortType);
    });

  }).fail((xhr, status, error) => {
    handleDataError($errorContainer);
  });
}

function makeKPIGraph(settings) {
  let $container = settings.container;
  let fetchDataset = getChartData($container.data('url'), 'objects');
  let $errorContainer = $container.children('div');
  fetchDataset.done(data => {
    new k.Graph($container, {
      data: {
        datums: data,
        seriesSpec: settings.descriptors
      },
      options: {
        legend: 'mini',
        slider: true,
        bucket: settings.bucket
      },
      graph: {
        width: 880,
        height: 300
      },
    }).render();
  }).fail((xhr, status, error) => {
    handleDataError($errorContainer);
  });
}
