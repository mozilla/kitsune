(function() {

function init() {
  makeTopicsGraph();
  makeMetricsGraph();
}

function makeTopicsGraph() {
  var $topic, datums, seriesSpec, key;

  $('input[type=date]').datepicker({
    dateFormat: 'yy-mm-dd'
  });

  $topics = $('#topic-stats');
  datums = $topics.data('graph');
  seriesSpec = [];
  window.datums = datums;

  var min = 3;

  for (key in datums[0]) {
    if (key === 'date' || !datums[0].hasOwnProperty(key)) continue;
    // TODO: these names should be localized.
    seriesSpec.push({
      name: key,
      slug: key,
      func: k.Graph.identity(key)
    });
  }

  new k.Graph($topics, {
    data: {
      datums: datums,
      seriesSpec: seriesSpec
    },
    graph: {
      renderer: 'bar',
      width: 690,
      unstack: false
    },
    options: {
      slider: false
    }
  }).render();
}

function makeMetricsGraph() {
  var $container = $('#questions-metrics');
  $.getJSON($container.data('url'), function(data) {
    new k.Graph($container, {
      data: {
        datums: data.objects,
        seriesSpec: [
          {
            name: gettext('Questions'),
            slug: 'questions',
            func: k.Graph.identity('questions'),
            color: '#5d84b2',
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
            name: gettext('% Responded in 24 hours'),
            slug: 'responded_24',
            func: k.Graph.fraction('responded_24', 'questions'),
            color: '#89a54e',
            axisGroup: 'percent',
            type: 'percent'
          },
          {
            name: gettext('% Responded in 72 hours'),
            slug: 'responded_72',
            func: k.Graph.fraction('responded_72', 'questions'),
            color: '#80699b',
            axisGroup: 'percent',
            type: 'percent'
          }
        ]
      },
      options: {
        legend: 'mini',
        slider: true,
        bucket: true
      },
      graph: {
        width: 880,
        height: 300
      },
    }).render();
  });
}

$(document).ready(init);

})();
