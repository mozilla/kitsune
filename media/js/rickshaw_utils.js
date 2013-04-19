(function($) {

window.k = k || {};

function findOrMakeElem(parent, selector, elemString) {
  var $elem = $(parent).find(selector);
  if (!$elem.length) {
    $elem = $(elemString).appendTo(parent);
  }
  return $elem;
}

/* class Graph */
k.Graph = function($elem, extra) {
  var defaults = {
    toRender: [],
    options: {
      legend: true,
      slider: true,
      xAxis: true,
      yAxis: true,
      hover: true,
      sets: false,
      bucket: false
    },

    data: {
      series: [],
      annotations: [],
      bucketed: []
    },

    metadata: {
      colors: {},
      sets: {},
      bucketMethods: {}
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
  window.G = this;
  this.initBucketUI();
  this.initData();
  this.initGraph();
  this.initMetadata();
  this.initSlider();
  this.initAxises();
  this.initLegend();
  this.initSets();
};

k.Graph.prototype.initData = function() {
  var buckets;
  var i, j, d;
  var key;
  var line;
  // Empty the list.
  this.data.bucketed.splice(0, this.data.bucketed.length);

  if (this.data.bucketSize) {

    for (i=0; i < this.data.series.length; i++) {
      line = this.data.series[i];
      buckets = {};

      for (j=0; j < line.data.length; j++) {
        // make a copy.
        d = $.extend({}, line.data[j]);
        d.x = Math.floor(d.x / this.data.bucketSize) * this.data.bucketSize;

        if (buckets[d.x] === undefined) {
          buckets[d.x] = [d];
        } else {
          buckets[d.x].push(d);
        }
      }

      this.data.bucketed.push({
        name: line.name,
        slug: line.slug,
        disabled: line.disabled,
        color: line.color,
        data: $.map(buckets, function(dList) {
          var sum = 0, i, method, out;
          out = $.extend({}, dList[0]);

          for (i=0; i < dList.length; i++) {
            sum += dList[i].y;
          }

          method = this.metadata.bucketMethods[line.slug];
          if (method === 'average') {
            out.y = sum / dList.length;
          } else {
            out.y = sum;
          }

          return out;
        }.bind(this))
      });
    }

  } else {
    this.data.bucketed = this.data.series.slice();
  }
};

k.Graph.prototype.initMetadata = function() {
  var series, key, i;

  this.data.lines = {};
  series = this.data.series;
  for (i=0; i < series.length; i++) {
      s = series[i];
      this.data.lines[s.slug] = s;
  }

  for (key in this.metadata.colors) {
    if (!this.metadata.colors.hasOwnProperty(key)) continue;
    this.data.lines[key].color = this.metadata.colors[key];
  }
};

k.Graph.prototype.getGraphData = function() {
  var palette = new Rickshaw.Color.Palette();
  var series = new Rickshaw.Series(this.data.bucketed, palette);

  series.active = function() {
    // filter by active.
    return $.map(this, function(s) {
      if (!s.disabled) {
        return s;
      }
    });
  };

  return series;
};

k.Graph.prototype.initBucketUI = function() {
  if (!this.options.bucket) return;

  var i;
  var DAY_S = 24 * 60 * 60;
  var bucketSizes = [
    {value: 1 * DAY_S, text: gettext('Daily')},
    {value: 7 * DAY_S, text: gettext('Weekly')},
    {value: 30 * DAY_S, text: gettext('Monthly')}
  ];

  var $bucket = $('<div class="bucket"></div>')
    .appendTo(this.dom.elem.find('.inline-controls'));
  var $select = $('<select>');

  for (i=0; i < bucketSizes.length; i++) {
    $('<option name="bucketing">')
      .val(bucketSizes[i].value)
      .text(bucketSizes[i].text)
      .appendTo($select);
  }
  $bucket.append($select);

  var self = this;
  $select.on('change', function() {
    self.data.bucketSize = parseInt($(this).val(), 10);
    self.update();
  });
};

k.Graph.prototype._xFormatter = function(seconds) {
  var DAY_S = 24 * 60 * 60;

  var sizes = {};
  sizes[7 * DAY_S] = gettext('Week beginning %(year)s-%(month)s-%(date)s');
  sizes[30 * DAY_S] = gettext('Month beginning %(year)s-%(month)s-%(date)s');

  console.log(sizes);
  var key = this.data.bucketSize;
  console.log('key: ' + key + ' -> ' + sizes[key]);
  var format = sizes[key];
  if (format === undefined) {
    format = '%(year)s-%(month)s-%(date)s';
  }

  return k.dateFormat(format, new Date(seconds * 1000));
};

k.Graph.prototype._yFormatter = function(value) {
  if (value > 0 && value <= 1.0) {
    // This is probably a percentage.
    return Math.floor(value * 100) + '%';
  } else {
    return Math.floor(value);
  }
};

k.Graph.prototype.initGraph = function() {
  var hoverClass;
  var key;
  var series;
  var i;
  this.dom.graph = this.dom.elem.find('.graph');

  var graphOpts = $.extend({
    element: this.dom.graph[0], // Graph can't handle jQuery objects.
    series: this.getGraphData(),
    interpolation: 'linear'
  }, this.graph);

  this.dom.elem.find('.graph').empty();
  this.rickshaw.graph = new Rickshaw.Graph(graphOpts);

  if (this.options.hover) {
    var hoverOpts = $.extend({
      xFormatter: this._xFormatter.bind(this),
      yFormatter: this._yFormatter.bind(this),
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
  var minDate;

  if (this.options.slider) {
    this.dom.slider = this.dom.elem.find('.slider');
    this.dom.slider.empty();

    this.dom.elem.find('.inline-controls').append('<div><label for="slider"/></div>');

    slider = new Rickshaw.Graph.RangeSlider({
      graph: this.rickshaw.graph,
      element: this.dom.slider
    });

    this.slider = slider.element;

    // About 6 months ago, as epoch seconds.
    minDate = (new Date() - (1000 * 60 * 60 * 24 * 180)) / 1000;
    this.rickshaw.graph.window.xMin = minDate;
    this.rickshaw.graph.update();

    this.slider.slider('values', 0, minDate);
    function onSlide(event, ui) {
        var start = new Date(ui.values[0] * 1000);
        var end = new Date(ui.values[1] * 1000 - (1000 * 60 * 60 * 24));
        var fmt = '%(year)s-%(month)s-%(date)s';
        var label = interpolate('From %s to %s', [k.dateFormat(fmt, start),
                                                  k.dateFormat(fmt, end)]);
        $('label[for=slider]').text(label);
    }
    this.slider.on('slide', onSlide);
    onSlide(null, {values: this.slider.slider('values')} );
  }
};

k.Graph.prototype.initAxises = function() {
  var yAxis;

  if (this.options.xAxis) {
    xAxis = new Rickshaw.Graph.Axis.Time({
      graph: this.rickshaw.graph
    });
  }

  if (this.options.yAxis) {
    this.dom.yAxis = this.dom.elem.find('.y-axis');
    this.dom.yAxis.empty();

    yAxis = new Rickshaw.Graph.Axis.Y({
      graph: this.rickshaw.graph,
      orientation: 'left',
      element: this.dom.elem.find('.y-axis')[0]
    });
    this.toRender.push(yAxis);
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
  var i, j;

  if (this.options.timeline) {
    this.dom.timelines = $container.find('.timelines');
    this.rickshaw.timelines = [];

    for (i=0; i < this.data.annotations.length; i++) {
      annot = this.data.annotations[i];
      $timeline = $('<div class="timeline"/>').appendTo($timelines);

      timeline = new Rickshaw.Graph.Annotate({
        'graph': this.rickshaw.graph,
        'element': $timeline[0]
      });

      for (j=0; j < annot.data.length; j++) {
        timeline.add(annot.data[j].x, annot.data[j].text);
      }

      this.rickshaw.timelines.push(timeline);
    }
  }
};

k.Graph.prototype.initSets = function() {
  if (!this.options.sets) return;

  var key;
  var $sets = $('<div class="sets"></div>');

  for (key in this.metadata.sets) {
    if (!this.metadata.sets.hasOwnProperty(key)) continue;

    $('<input type="radio" name="sets"/>').val(key).appendTo($sets);
    $('<label for="sets">').text(key).appendTo($sets);
  }

  var self = this;
  $sets.on('change', 'input[name=sets]', function() {
    var $this = $(this);
    var lineName, set, i;

    for (lineName in self.metadata.sets) {
      set = self.metadata.sets[lineName];
      for (i=0; i < set.length; i++) {
        // Check or uncheck the line based on it's presence in a set and
        // the radio's value.
        disabled = !!(($this.attr('value') === lineName) ^ $this.prop('checked'));
        self.data.lines[set[i]].disabled = disabled;
      }
    }

    self.update();
  });


  this.dom.elem.find('.inline-controls').append($sets);
  $sets.find('input[name=sets]').first().click();
};

k.Graph.prototype.render = function() {
  var i;

  for (i=0; i < this.toRender.length; i++) {
    this.toRender[i].render();
  }

  if (this.options.yAxis) {
    this.dom.yAxis.css({'top': this.dom.graph.position().top});
  }
};

k.Graph.prototype.update = function() {
  var newSeries, i;

  this.initData();

  this.rickshaw.graph.series = this.getGraphData();
  this.rickshaw.graph.stackedData = false;
  this.rickshaw.graph.update();

  this.initMetadata();
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