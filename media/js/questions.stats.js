(function() {

function init() {
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
      renderer: 'bar'
    },
    options: {
      slider: false
    }
  }).render();
}

$(document).ready(init);

})();
