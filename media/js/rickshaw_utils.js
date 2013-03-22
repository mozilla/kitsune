(function($) {

window.k = k || {};
window.k.rickshaw = {};

k.rickshaw.prepareData = function(data) {
  var palette = new Rickshaw.Color.Palette();
  return new Rickshaw.Series(data, palette);
};

k.rickshaw.makeGraph = function($elem, data, options) {
  options = $.extend({
    graph: {
      renderer: 'bar'
    },
    annotations: false,
  }, options);

  var i;
  var render = [];
  var graph;
  var hoverClass, hoverDetail;
  var $legend, legend;
  var $yaxis, xaxis, yaxis;
  var $slider, slider;

  render = [];

  $elem.find('.graph, .legend, .y-axis').empty();
  graph = new Rickshaw.Graph({
    element: $elem.find('.graph')[0],
    series: k.rickshaw.prepareData(data),
    renderer: options.graph.renderer,
    interpolation: 'linear'
  });
  render.push(graph);

  if (options.graph.renderer === 'bar') {
    hoverClass = Rickshaw.Graph.BarHoverDetail;
  } else {
    hoverClass = Rickshaw.Graph.HoverDetail;
  }
  hoverDetail = new hoverClass({
    graph: graph
  });

  $legend = $elem.find('.legend');
  if ($legend.length) {
    legend = new Rickshaw.Graph.Legend( {
      graph: graph,
      element: $legend[0]
    });

    new Rickshaw.Graph.Behavior.Series.Toggle({
      graph: graph,
      legend: legend
    });

    new Rickshaw.Graph.Behavior.Series.Order({
      graph: graph,
      legend: legend
    });
    render.push(legend);
  }

  $yaxis = $elem.find('.y-axis');
  if ($yaxis.length) {
    xaxis = new Rickshaw.Graph.Axis.Time({
      graph: graph
    });

    yaxis = new Rickshaw.Graph.Axis.Y({
      graph: graph,
      orientation: 'left',
      element: $elem.find('.y-axis')[0]
    });
    render.push(yaxis);
  }

  $slider = $elem.find('.slider');
  if ($slider.length) {
    slider = new Rickshaw.Graph.RangeSlider({
      graph: graph,
      element: $slider
    });
  }

  for (i=0; i<render.length; i++) {
    render[i].render();
  }

  $yaxis.css({'top': $elem.find('.graph').position().top});

  return {
    'graph': graph,
    'slider': slider.element
  };
};


Rickshaw.namespace('Rickshaw.Graph.BarHoverDetail');

/* This is a mostly intact version of Rickshaw.Graph.HoverDetail that
 * is modified to work nicer with the Bar renderer. The data point
 * chosen is based on the rectangle rendered by the Bar renderer, and
 * the tool tip points to the center of that rectangle.
 *
 * The `update` method has changed to modify the hover behavior, and the
 * `render` method has changed to modify the tool tip behavior.
 */

Rickshaw.Graph.BarHoverDetail = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {

  update: function(e) {

    e = e || this.lastEvent;
    if (!e) return;
    this.lastEvent = e;

    if (!e.target.nodeName.match(/^(path|svg|rect)$/)) return;

    var graph = this.graph;
    var barWidth = graph.renderer.barWidth() + graph.renderer.gapSize;

    var eventX = e.offsetX || e.layerX;
    var eventY = e.offsetY || e.layerY;

    var j = 0;
    var points = [];
    var nearestPoint;

    // Iterate through each series, and find the point that most closely
    // matches the mouse pointer.
    this.graph.series.active().forEach( function(series) {

      var data = this.graph.stackedData[j++];
      var domainX = graph.x.invert(eventX);

      var domainIndexScale = d3.scale.linear()
        .domain([data[0].x, data.slice(-1)[0].x])
        .range([0, data.length - 1]);

      var approximateIndex = Math.round(domainIndexScale(domainX));
      var dataIndex = Math.min(approximateIndex || 0, data.length - 1);

      var i = approximateIndex;
      while (i < data.length - 1) {

        if (!data[i] || !data[i + 1]) break;

        if (data[i].x <= domainX && data[i + 1].x > domainX) {
          dataIndex = i;
          break;
        }

        if (data[i + 1].x <= domainX) { i++; } else { i--; }
      }

      if (dataIndex < 0) dataIndex = 0;
      var value = data[dataIndex];

      var left = graph.x(value.x);
      var right = left + barWidth;
      var bottom = graph.y(value.y0);
      var top = graph.y(value.y + value.y0);

      var point = {
        series: series,
        value: value,
        order: j,
        name: series.name
      };

      if (left <= eventX && eventX < right &&
          top <= eventY && eventY < bottom) {

        nearestPoint = point;
      }

      points.push(point);

    }, this );

    var renderArgs = {
      points: points,
      detail: points,
      mouseX: eventX,
      mouseY: eventY
    };

    if (nearestPoint) {
      nearestPoint.active = true;
    }

    if (this.visible) {
      this.render(renderArgs);
    }
  },

  render: function(args) {

    var graph = this.graph;
    var points = args.points;
    var barWidth = graph.renderer.barWidth() + graph.renderer.gapSize;

    var point = points.filter(function(p) {return p.active;}).shift();

    if (!point || point.value.y === null) {
      return;
    }

    var formattedXValue = this.xFormatter(point.value.x);
    var formattedYValue = this.yFormatter(point.value.y);

    this.element.innerHTML = '';
    this.element.style.left = (graph.x(point.value.x) + barWidth / 2) + 'px';

    var xLabel = document.createElement('div');

    xLabel.className = 'x_label';
    xLabel.innerHTML = formattedXValue;
    this.element.appendChild(xLabel);

    var item = document.createElement('div');

    item.className = 'item';
    item.innerHTML = this.formatter(point.series, point.value.x, point.value.y,
                                    formattedXValue, formattedYValue, point);
    item.style.top = this.graph.y(point.value.y0 + point.value.y / 2) + 'px';

    this.element.appendChild(item);

    var dot = document.createElement('div');

    dot.className = 'dot';
    dot.style.top = item.style.top;
    dot.style.borderColor = point.series.color;

    this.element.appendChild(dot);

    if (point.active) {
      item.className = 'item active';
      dot.className = 'dot active';
    }

    this.show();

    if (typeof this.onRender == 'function') {
      this.onRender(args);
    }
  }
});

})(jQuery);