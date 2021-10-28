import "jquery-ui/ui/widgets/datepicker";

(function() {

  function init() {
    makeTopicsGraph();
    makeMetricsGraph();
  }

  function makeTopicsGraph() {
    var $topics, datums, seriesSpec, key;

    $('input[type=date]').attr('type','text').datepicker({
      dateFormat: 'yy-mm-dd'
    });

    $topics = $('#topic-stats');
    if ($topics.length === 0) {
      return;
    }

    datums = $topics.data('graph');
    seriesSpec = [];

    for (key in datums[0]) {
      if (key === 'date' || !datums[0].hasOwnProperty(key)) {
        continue;
      }
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
      var objects = data.objects;
      objects.forEach(function(object) {
        object.questions = object.questions || 0;
        object.solved = object.solved || 0;
        object.responded_24 = object.responded_24 || 0;
        object.responded_72 = object.responded_72 || 0;
      });

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
