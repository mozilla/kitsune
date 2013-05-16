(function($) {

// TODO: Figure out why this one causes strange errors.
//"use strict";

window.k = k || {};

/* class Graph */
k.Graph = function($elem, extra) {
  var defaults = {
    toRender: [],
    options: {
      bucket: false,
      daterange: true,
      hover: true,
      legend: true,
      sets: false,
      slider: true,
      xAxis: true,
      yAxis: true
    },

    data: {
      datums: [],
      seriesSpec: [],

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
    yAxis: {},

    rickshaw: {},
    dom: {},
    axisGroups: {},
    d3: {
      axises: {}
    }
  };

  // true means deep.
  $.extend(true, this, defaults, extra);

  this.dom.elem = $elem;

  this.init();
};

k.Graph.prototype.init = function() {
  this.initBucketUI();
  this.initData();
  this.initGraph();
  this.initAxises();
  this.initSlider();
  this.initDateRange();
  this.initLegend();
  this.initSets();
};

k.Graph.prototype.initData = function() {
  var buckets = {};
  var bucketed = [];
  var i, d, key;
  var axisGroup, axis;
  var series, name;

  // Bucket data
  if (this.data.bucketSize) {
    for (i = 0; i < this.data.datums.length; i++) {
      // make a copy.
      d = $.extend({}, this.data.datums[i]);
      d.date = Math.floor(d.date / this.data.bucketSize) * this.data.bucketSize;

      if (buckets[d.date] === undefined) {
        buckets[d.date] = [d];
      } else {
        buckets[d.date].push(d);
      }
    }

    bucketed = $.map(buckets, function(dList) {
      var sum = 0, i, method, out;
      var key;
      out = $.extend({}, dList[0]);

      for (key in out) {
        if (key === 'date' || !out.hasOwnProperty(key)) continue;

        for (i = 1; i < dList.length; i++) {
          out[key] += dList[i][key];
        }
      }

      return out;
    });

  } else {
    bucketed = this.data.datums.slice();
  }

  this.data.series = this.makeSeries(bucketed, this.data.seriesSpec);

  // Scale data based on axis groups
  this.axisGroups = {};
  for (i = 0; i < this.data.series.length; i++) {
    series = this.data.series[i];
    name = series.axisGroup;
    if (this.axisGroups[name] === undefined) {
      this.axisGroups[name] = {
        max: -Infinity
      };
    }
    this.axisGroups[name].max = Math.max(this.axisGroups[name].max, series.max);
  }

  for (i = 0; i < this.data.series.length; i++) {
    series = this.data.series[i];
    axisGroup = this.axisGroups[series.axisGroup];
    series.data = _.map(series.data, function(point) {
      return {
        x: point.x,
        y: point.y / axisGroup.max
      };
    });
    series.scale = axisGroup.max;
    axis = this.d3.axises[series.axisGroup];
    if (axis) {
      axis.setScale(axisGroup.max);
    }
  }
};

/* Take an array of datums and make a set of named x/y series, suitable
 * for Rickshaw. Each series is generated by one of the key functions.
 *
 * `descriptors` is an array of objects that define a name, a slug, and
 * a function to calculate data. Each data function will be used as a
 * map function on the datum objects to generate a series.
 *
 * Each descriptor may also optionally contain:
 *   color: The color to draw this series in. The default is to use a
 *       color generated by rickshaw.
 *   disabled: If true, this graph will not be drawn. The default is
 *       false.
 *   axisGroup: The name of the axisGroup this series belongs to.
 *
 * Output will have all the above values, as well as the maximum
 * values within the current graph window.
 */
k.Graph.prototype.makeSeries = function(objects, descriptors) {
  var i;
  var datum, series = [];
  var split, date;
  var desc;
  var max, data;
  var windowMin, windowMax;

  if (this.rickshaw.graph) {
    windowMin = this.rickshaw.graph.window.xMin || -Infinity;
    windowMax = this.rickshaw.graph.window.xMax || +Infinity;
  } else {
    windowMin = -Infinity;
    windowMax = +Infinity;
  }

  for (i = 0; i < descriptors.length; i++) {
    max = -Infinity;
    desc = descriptors[i];

    data = _.map(objects, function(datum) {
      var val = desc.func(datum);

      if (isNaN(val) ) {
        val = 0;
      }

      if (windowMin <= datum.date && datum.date <= windowMax) {
        max = Math.max(max, val);
      }

      return {x: datum.date, y: val};
    });

    if (max <= 0 || isNaN(max) || !isFinite(max)) {
      max = 1;
    }

    series[i] = {
      name: desc.name,
      slug: desc.slug,
      color: desc.color,
      disabled: desc.disabled || false,
      axisGroup: desc.axisGroup,
      max: max,
      data: data
    };
  }

  // Rickshaw gets angry when its data isn't sorted.
  for (i = 0; i < descriptors.length; i++) {
    series[i].data.sort(function(a, b) { return a.x - b.x; });
  }

  return series;
};

k.Graph.prototype.getGraphData = function() {
  var palette = new Rickshaw.Color.Palette();
  var series = new Rickshaw.Series(this.data.series, palette);

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
    self.initData();
    self.update();
  });
};

k.Graph.prototype._xFormatter = function(seconds) {
  var DAY_S = 24 * 60 * 60;

  var sizes = {};
  sizes[7 * DAY_S] = gettext('Week beginning %(year)s-%(month)s-%(date)s');
  sizes[30 * DAY_S] = gettext('Month beginning %(year)s-%(month)s-%(date)s');

  var key = this.data.bucketSize;
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
  var i, key;
  var series;
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

    if (this.graph.renderer === 'bar') {
      hoverClass = Rickshaw.Graph.ScaledBarHoverDetail;
    } else {
      hoverClass = Rickshaw.Graph.ScaledHoverDetail;
    }

    this.rickshaw.hover = new hoverClass(hoverOpts);
  }

  this.toRender.push(this.rickshaw.graph);
};

k.Graph.prototype.initSlider = function() {
  var self = this;
  var now, minDate, ytd_ago, all_ago;
  var $inlines, $slider, $presets;
  var self = this;
  var DAY = 24 * 60 * 60;

  if (this.options.slider) {
    this.dom.slider = this.dom.elem.find('.slider');
    this.dom.slider.empty();

    slider = new Rickshaw.Graph.RangeSlider({
      graph: this.rickshaw.graph,
      element: this.dom.slider
    });

    this.slider = slider.element;

    // About 6 months ago, as epoch seconds.
    minDate = (+new Date() - (1000 * 60 * 60 * 24 * 180)) / 1000;
    this.rickshaw.graph.window.xMin = minDate;

    this.initData();
    this.update();

    this.slider.slider('values', 0, minDate);
    function onSlide() {
      self.initData();
      self.update();
    }
    this.slider.on('slide', onSlide);
  }
};

k.Graph.prototype.initDateRange = function() {
  var self = this;
  var now, minDate, ytd_ago, all_ago;
  var $inlines, $slider, $presets;
  var DAY = 24 * 60 * 60;

  now = new Date();
  ytd_ago = (now - new Date(now.getFullYear(), 0, 0)) / 1000;
  all_ago = ((now / 1000) - this.data.series[0].data[0].x);

  presets = [
    [30 * DAY, gettext('1m', 'Short for 1 month')],
    [90 * DAY, gettext('3m', 'Short for 3 months')],
    [180 * DAY, gettext('6m', 'Short for 6 months')],
    [ytd_ago, gettext('YTD', 'Short "Year to Date"')],
    [365 * DAY, gettext('1y', 'Short for 1 year')],
    [all_ago, gettext('All')]
  ];

  if (this.options.daterange) {
    $inlines = this.dom.elem.find('.inline-controls');
    $label = $('<label for="slider"/>')
      .html('From <input type="date" name="start"/> to <input type="date" name="end"/>')
      .appendTo($('<div class="range"/>').appendTo($inlines));
    $presets = $('<div class="range-presets"/>').appendTo($inlines);

    $label.find('input[type=date]').datepicker({
      dateFormat: 'yy-mm-dd'
    });

    $label.on('change', 'input', function() {
      var $this = $(this);
      var val = $this.val();
      if ($this.prop('name') == 'start') {
        self.setRange(val, undefined);
      } else {
        self.setRange(undefined, val);
      }
    });

    this.rickshaw.graph.onUpdate(function() {
      var window = self.rickshaw.graph.window;

      var now = +new Date() / 1000;
      var start = window.xMin || (now - all_ago);
      var end = window.xMax || now;

      if (self.options.slider) {
        self.slider.slider('values', [start, end]);
      }

      start = new Date(start * 1000);
      end = new Date(end * 1000);

      var fmt = '%(year)s-%(month)s-%(date)s';
      $label.find('[name=start]').val(k.dateFormat(fmt, start));
      $label.find('[name=end]').val(k.dateFormat(fmt, end));
    });

    for (i = 0; i < presets.length; i++) {
      $('<button />')
        .data('days-ago', presets[i][0])
        .text(presets[i][1])
        .appendTo($presets)
        .on('click', function() {
          var now = +new Date() / 1000;
          var min = (now - $(this).data('days-ago'));

          self.rickshaw.graph.window.xMin = min;
          self.rickshaw.graph.window.xMax = undefined;
          if (self.options.slider) {
            self.slider.slider('values', [min, now]);
          }

          self.initData();
          self.update();
        });
    }
  }
};

k.Graph.prototype.initAxises = function() {
  var axis, key, opts, i;
  this.d3.axises = {};

  if (this.options.xAxis) {
    new Rickshaw.Graph.Axis.Time({
      graph: this.rickshaw.graph
    });
  }

  if (this.options.yAxis) {
    this.dom.yAxis = this.dom.elem.find('.y-axis');
    this.dom.yAxis.empty();

    opts = $.extend({
      graph: this.rickshaw.graph,
      orientation: 'left',
      tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
      element: this.dom.elem.find('.y-axis')[0],
      side: 'left'
    }, this.yAxis);

    i = 0;
    for (key in this.axisGroups) {
      if (!this.axisGroups.hasOwnProperty(key)) continue;
      opts.scale = this.axisGroups[key].max;
      opts.side = ['left', 'right'][i++];
      axis = new Rickshaw.Graph.Axis.ScaledY(opts);
      this.toRender.push(axis);
      this.d3.axises[key] = axis;
    }
  }
};

k.Graph.prototype.initLegend = function() {
  if (this.options.legend == 'mini') {

    var i;
    var series, line;
    var $legend, $series, $li;

    $legend = $('<div class="legend"></div>')
      .appendTo(this.dom.elem.find('.inline-controls'));
    $series = $('<ul>');

    for (i=0; i < this.data.series.length; i++) {
      line = this.data.series[i];
      $li = $('<li>').appendTo($series);
      $('<span class="color-square">')
        .css('background', line.color)
        .appendTo($li);
      $('<span>').text(line.name).appendTo($li);
    }

    $legend.append($series);

  } else if (this.options.legend) {

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

    $('<input type="checkbox" name="sets"/>').val(key).appendTo($sets);
    $('<label for="sets">').text(key).appendTo($sets);
  }

  var self = this;
  $sets.on('change', 'input[name=sets]', function() {
    var count = 0;
    $sets.find('input[name=sets]').each(function() {
      count += !!$(this).prop('checked');
    });
    if (count === 0) {
      $(this).prop('checked', true);
      return;
    }

    var $this = $(this);
    var set = self.metadata.sets[$this.attr('value')];
    var disabled = !$this.prop('checked');

    for (i = 0; i < self.data.series.length; i++) {
      line = self.data.series[i];
      if (set.indexOf(line.slug) !== -1) {
        line.disabled = disabled;
        self.data.seriesSpec[i].disabled = disabled;
      }
    }

    self.update();
  });

  this.dom.elem.find('.inline-controls').append($sets);
  $sets.find('input[name=sets]').prop('checked', true);
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

  this.rickshaw.graph.series = this.getGraphData();
  this.rickshaw.graph.stackedData = false;
  this.rickshaw.graph.update();
};

/* Accepts start and end as one of:
 *  - Seconds since epoch
 *  - Date objects
 *  - Strings formatted as YYYY-MM-DD
 */
k.Graph.prototype.setRange = function(start, end) {
  var window = this.rickshaw.graph.window;

  if (start === undefined) {
    start = window.xMin;
  }
  if (end === undefined) {
    end = window.xMax;
  }

  start = k.Graph.toSeconds(start);
  end = k.Graph.toSeconds(end);

  window.xMin = start;
  window.xMax = end;
  this.initData();
  this.update();
};
/* end Graph */

/* These are datum transforming methods. They take an object like
 * {created: 1367270055, foo: 10, bar: 20, baz: 30} and return a number.
 */

// Returns the value associated with a key.
// identity('foo') -> 10
k.Graph.identity = function(key) {
  return function(d) {
    return d[key];
  };
};

// Divides the first key by the second.
// fraction('foo', 'bar') -> 0.5
k.Graph.fraction = function(topKey, bottomKey) {
  return function(d) {
    return d[topKey] / d[bottomKey];
  };
};

// Takes a date in one of the followign formats and returns seconds
// since the epoch: Date objects, strings in the format 'YYYY-MM-DD',
// Integers in second since the epoch form..
k.Graph.toSeconds = function(obj) {
  var type = typeof obj;
  if (type === 'object') {
    return obj / 1000;
  }
  if (type === 'string') {
    var split = obj.split('-');
    // Date constructer takes months as 0-based.
    var date = new Date(split[0], split[1] - 1, split[2]);
    return date / 1000;
  }
  if (type === 'number') {
    return obj;
  }
  return undefined;
}

/* Takes two or more arguments. The arguments are the keys that
 * represent an entire collection (all pieces in a pie). The first key
 * is the current slice of the pie. Returns what percent the first key
 * is of the total, as a decimal between 0.0 and 1.0.
 *
 * percentage('foo', 'bar', 'baz') -> 10 / (10 + 20 + 30) = ~0.166
 */
k.Graph.percentage = function(partKey /* *restKeys */) {
  var allKeys = Array.prototype.slice.call(arguments);
  return function(d) {
    var sum = 0;
    _.each(allKeys, function(key) {
      sum += d[key];
    });
    return d[partKey] / sum;
  };
};


Rickshaw.namespace('Rickshaw.Graph.ScaledHoverDetail');

/* This is a mostly intact version of Rickshaw.Graph.HoverDetail that
 * is modified to work with scaled series.
 *
 * The `render` method has changed to call a method to determine the
 * location of the tooltip, and to respect series scale (`series.scale`).
 */

Rickshaw.Graph.ScaledHoverDetail = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {

  getHoverPoint: function(point) {
    var barWidth = this.graph.renderer.barWidth + this.graph.renderer.gapSize;
    return {
      left: this.graph.x(point.value.x),
      top: this.graph.y(point.value.y0 + point.value.y)
    };
  },

  render: function(args) {

    var graph = this.graph;
    var points = args.points;
    var point = points.filter( function(p) { return p.active; } ).shift();

    if (!point || point.value.y === null) return;

    var scaledY = point.value.y * (point.series.scale || 1);
    var formattedXValue = this.xFormatter(point.value.x);
    var formattedYValue = this.yFormatter(scaledY);

    var hoverPoint = this.getHoverPoint(point);

    this.element.innerHTML = '';
    this.element.style.left = hoverPoint.left + 'px';

    var xLabel = document.createElement('div');

    xLabel.className = 'x_label';
    xLabel.innerHTML = formattedXValue;
    this.element.appendChild(xLabel);

    var item = document.createElement('div');

    item.className = 'item';
    item.innerHTML = this.formatter(point.series, point.value.x, point.value.y, formattedXValue, formattedYValue, point);
    item.style.top = hoverPoint.top + 'px';

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

/* This is a mostly intact version of Rickshaw.Graph.ScaledHoverDetail that
 * is modified to work nicer with the Bar renderer. The data point
 * chosen is based on the rectangle rendered by the Bar renderer, and
 * the tool tip points to the center of that rectangle.
 *
 * The `update` method has changed to modify the hover behavior.
 */
Rickshaw.namespace('Rickshaw.Graph.ScaledBarHoverDetail');
Rickshaw.Graph.ScaledBarHoverDetail = Rickshaw.Class.create(Rickshaw.Graph.ScaledHoverDetail, {

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

  getHoverPoint: function(point) {
    var barWidth = this.graph.renderer.barWidth() + this.graph.renderer.gapSize;
    return {
      left: this.graph.x(point.value.x) + barWidth / 2,
      top: this.graph.y(point.value.y0 + point.value.y / 2)
    };
  }

});


Rickshaw.namespace('Rickshaw.Graph.Axis');

Rickshaw.Graph.Axis.ScaledY = function(args) {
  this.graph = args.graph;
  this.side = args.side || 'left';
  this.scale = args.scale || 1.0;
  this.tickFormat = args.tickFormat || function(v) { return v; };

  var pixelsPerTick = args.pixelsPerTick || 75;
  this.ticks = args.ticks || Math.floor(this.graph.height / pixelsPerTick);

  var $axis = $('<div class="multi-y-axis" />');

  if (this.side === 'left') {
    $(this.graph.element).parent()
      .before($axis)
      .css('margin-left', '10px');
  } else {
    $(this.graph.element).parent()
      .after($axis)
      .css('margin-right', '20px');
  }

  var oldWidth = $(this.graph.element).outerWidth();
  this.graph.setSize({width: oldWidth - $axis.outerWidth()});

  $axis.css('height', $(this.graph.element).innerHeight());

  this.element = $axis[0];
  this.graph.onUpdate(this.render);
};

Rickshaw.Graph.Axis.ScaledY.prototype.render = function() {
  var w = $(this.element).innerWidth();
  var h = $(this.element).innerHeight();
  var scale, axis, svg, group;

  d3.select(this.element).select('*').remove();

  padding = 10;
  scale = d3.scale.linear()
    .domain([this.scale, 0])
    .range([padding, h - padding]);

  axis = d3.svg.axis()
    .scale(scale)
    .orient(this.side)
    .tickFormat(this.tickFormat);

  svg = d3.select(this.element).append('svg:svg')
    .attr('width', w)
    .attr('height', h)
    .attr('class', 'rickshaw_graph y_axis');

  group = svg.append('svg:g')
    .attr('class', 'y_ticks plain')
    .call(axis);
  if (this.side === 'left') {
    group.attr('transform', 'translate(40, 0)');
  } else {
    group.select('path.domain').attr('style', 'transform: translate(1px, 0)');
  }
};

Rickshaw.Graph.Axis.ScaledY.prototype.setScale = function(s) {
  this.scale = s || 1.0;
  this.render();
};

})(jQuery);