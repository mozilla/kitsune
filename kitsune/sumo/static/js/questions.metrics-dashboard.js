(function() {

function init() {
  makeTopicsGraph();
  makeMetricsGraph();
}

function makeTopicsGraph() {
  var $topics, datums, seriesSpec, key;

  $('input[type=date]').datepicker({
    dateFormat: 'yy-mm-dd'
  });

  $topics = $('#topic-stats');
  if ($topics.length === 0) {
    return;
  }

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
    // Fill in 0s so bucketing doesn't freak out...
    var object;
    var objects = data.objects;
    for (var i = 0, l = objects.length; i < l; i++) {
      object = objects[i];
      if(object.questions === undefined) {
        object.questions = 0;
      }
      if(object.solved === undefined) {
        object.solved = 0;
      }
      if(object.responded_24 === undefined) {
        object.responded_24 = 0;
      }
      if(object.responded_72 === undefined) {
        object.responded_72 = 0;
      }
    }

    new k.Graph($container, {
      data: {
        datums: objects,
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
