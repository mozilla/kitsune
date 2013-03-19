(function() {

function prepareData(data) {
  var palette = new Rickshaw.Color.Palette();
  return new Rickshaw.Series(data, palette);
}

function makeGraph($elem, data) {
  $elem.find('.graph, .legend, .y-axis').empty();
  var graph = new Rickshaw.Graph({element: $elem.find('.graph')[0], series: prepareData(data),
    renderer: 'bar'
  });

  var hoverDetail = new Rickshaw.Graph.BarHoverDetail( {
    graph: graph
  });

  var legend = new Rickshaw.Graph.Legend( {
    graph: graph,
    element: $elem.find('.legend')[0]
  });

  new Rickshaw.Graph.Behavior.Series.Toggle({
    graph: graph,
    legend: legend
  });

  new Rickshaw.Graph.Behavior.Series.Order({
    graph: graph,
    legend: legend
  });

  var xaxis = new Rickshaw.Graph.Axis.Time( {
    graph: graph
  });

  var yaxis = new Rickshaw.Graph.Axis.Y({
    graph: graph,
    orientation: 'left',
    element: $elem.find('.y-axis')[0]
  });

  graph.render();
  xaxis.render();
  yaxis.render();
}

function init() {
  $('input[type=date]').datepicker({
    dateFormat: 'yy-mm-dd'
  });

  $topics = $('#topic-stats');
  makeGraph($topics, $topics.data('histogram'));
}

$(document).ready(init);

})();
