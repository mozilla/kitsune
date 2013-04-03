(function($) {

window.k = k || {};

/* class Graph */
k.Graph = function($elem, extra) {
  var defaults = {
    toRender: [],
    options: {
      legend: true,
      slider: true,
      xaxis: true,
      yaxis: true,
      hover: true
    },

    data: {
      series: [],
      annotations: []
    },

    graph: {
      renderer: 'line',
      interpolation: 'linear'
    },
    hover: {},

    rickshaw: {},
    dom: {}
  };

  // true means deep.
  $.extend(true, this, defaults, extra);

  this.dom.elem = $elem;

  this.init();
};

k.Graph.prototype.init = function() {
  this.initGraph();
  this.initSlider();
  this.initAxises();
  this.initLegend();
};

k.Graph.prototype.prepareData = function() {
  var palette = new Rickshaw.Color.Palette();
  return new Rickshaw.Series(this.data.series, palette);
};

k.Graph.prototype.initGraph = function() {
  var hoverClass;
  this.dom.graph = this.dom.elem.find('.graph');

  var graphOpts = $.extend({
    element: this.dom.graph[0], // Graph can't handle jQuery objects.
    series: this.prepareData(),
    interpolation: 'linear'
  }, this.graph);

  this.dom.elem.find('.graph').empty();
  this.rickshaw.graph = new Rickshaw.Graph(graphOpts);

  if (this.options.hover) {
    var hoverOpts = $.extend({
      graph: this.rickshaw.graph
    }, this.hover);

    if (this.rickshaw.graph.renderer === 'bar') {
      hoverClass = Rickshaw.Graph.BarHoverDetail;
    } else {
      hoverClass = Rickshaw.Graph.HoverDetail;
    }

    this.rickshaw.hover = new hoverClass(hoverOpts);
  }

  this.toRender.push(this.rickshaw.graph);
};

k.Graph.prototype.initSlider = function() {
  if (this.options.slider) {
    this.dom.slider = this.dom.elem.find('.slider');
    this.dom.slider.empty();

    slider = new Rickshaw.Graph.RangeSlider({
      graph: this.rickshaw.graph,
      element: this.dom.slider
    });

    this.slider = slider.element;
  }
};

k.Graph.prototype.initAxises = function() {
  var yaxis;

  if (this.options.xaxis) {
    xaxis = new Rickshaw.Graph.Axis.Time({
      graph: this.rickshaw.graph
    });
  }

  if (this.options.yaxis) {
    this.dom.yaxis = this.dom.elem.find('.y-axis');
    this.dom.yaxis.empty();

    yaxis = new Rickshaw.Graph.Axis.Y({
      graph: this.rickshaw.graph,
      orientation: 'left',
      element: this.dom.elem.find('.y-axis')[0]
    });
    this.toRender.push(yaxis);
  }
};

k.Graph.prototype.initLegend = function() {
  if (this.options.legend) {
    this.dom.legend = this.dom.elem.find('.legend');
    this.dom.legend.empty();

    this.rickshaw.legend = new Rickshaw.Graph.Legend( {
      graph: this.rickshaw.graph,
      element: this.dom.legend[0] // legend can't handle jQuery objects
    });

    new Rickshaw.Graph.Behavior.Series.Toggle({
      graph: this.rickshaw.graph,
      legend: this.rickshaw.legend
    });

    new Rickshaw.Graph.Behavior.Series.Order({
      graph: this.rickshaw.graph,
      legend: this.rickshaw.legend
    });
  }
};

k.Graph.prototype.initTimeline = function() {
  var $timeline, timeline;

  if (this.options.timeline) {
    this.dom.timelines = $container.find('.timelines');
    this.rickshaw.timelines = [];

    for (i=0; i < this.data.annotations.length; i++) {
      annot = this.data.annotations[i];
      $timeline = $('<div class="timeline"/>').appendTo($timelines);

      timeline = new Rickshaw.Graph.Annotate({
        'graph': graph.rickshaw.graph,
        'element': $timeline[0]
      });

      for (j=0; j < annot.data.length; j++) {
        timeline.add(annot.data[j].x, annot.data[j].text);
      }

      this.rickshaw.timelines.push(timeline);
    }
  }
};

k.Graph.prototype.render = function() {
  for (i=0; i<this.toRender.length; i++) {
    this.toRender[i].render();
  }

  if (this.options.yaxis) {
    this.dom.yaxis.css({'top': this.dom.graph.position().top});
  }
};
/* end Graph */


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