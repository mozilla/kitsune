/* globals Rickshaw:false, k:false, $:false, _:false, interpolate:false, gettext:false, d3:false */
(function () {
  'use strict';

  window.k = k || {};

  /* class Graph */
  var Graph = function ($elem, extra) {
    var defaults = {
      toRender: [],
      options: {
        bucket: false,
        daterange: true,
        hover: true,
        init: true,
        legend: true,
        sets: false,
        slider: true,
        timeline: false,
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
        renderer: 'area',
        interpolation: 'linear',
        stroke: true,
        unstack: true
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

    // true means do a deep merge.
    $.extend(true, this, defaults, extra);

    this.dom.elem = $elem;

    if (this.options.init) {
      this.init();
    }
  };

  Graph.prototype.init = function () {
    window.G = this;
    this.initBucketUI();
    this.initData();
    this.initGraph();
    this.initAxises();
    this.initSlider();
    this.initDateRange();
    this.initLegend();
    this.initSets();
    this.initTimeline();
  };

  Graph.prototype.initData = function () {
    var i, d;
    for (i = 0; i < this.data.datums.length; i += 1) {
      d = this.data.datums[i];
      d.date = Graph.toSeconds(d.date || d.created || d.start);
      d.created = undefined;
      d.start = undefined;
    }

    this.rebucket();
  };

  Graph.prototype.rebucket = function () {
    var buckets, bucketed, i, d, axisGroup, axis, series, name, date, chopLimit, now;
    buckets = {};
    bucketed = [];

    // Bucket data
    if (this.data.bucketSize) {
      for (i = 0; i < this.data.datums.length; i += 1) {
        // make a copy.
        d = $.extend({}, this.data.datums[i]);
        date = new Date(d.date * 1000);

        // NB: These are resilient to borders in months and years because
        // JS's Date has the neat property that
        //   new Date(2013, 4, -1) === new Date(2013, 3, 29)
        //   new Date(2013, 0, -60) === new Date(2012, 10, 1)
        // This might be the only nice thing about JS's Date.
        switch (this.data.bucketSize) {
        case 'day':
          // Get midnight of today (ie, the boundary between today and yesterday)
          d.date = new Date(date.getFullYear(), date.getMonth(), date.getDate());
          break;
        case 'week':
          // Get the most recent Sunday.
          d.date = new Date(date.getFullYear(), date.getMonth(), date.getDate() - date.getDay());
          break;
        case 'month':
          // Get the first of this month.
          d.date = new Date(date.getFullYear(), date.getMonth(), 1);
          break;
        default:
          throw 'Unknown bucket size ' + this.data.bucketSize;
        }
        d.date = d.date / 1000;

        if (buckets[d.date] === undefined) {
          buckets[d.date] = [d];
        } else {
          buckets[d.date].push(d);
        }
      }

      bucketed = $.map(buckets, function (dList) {
        var out, key;
        out = $.extend({}, dList[0]);

        for (key in out) {
          if (out.hasOwnProperty(key) && key !== 'date') {
            for (i = 1; i < dList.length; i += 1) {
              out[key] += dList[i][key];
            }
          }
        }

        return out;
      });

    } else {
      bucketed = this.data.datums.slice();
    }

    /* Data points that are too near the present represent a UX problem.
     * The data in them is not representative of a full time period, so
     * they appear to be downward trending. `chopLimit` represents the
     * boundary of what is considered to be "too new".  Bug #876912. */
    now = new Date();
    if (this.data.bucketSize === 'week') {
      // Get most recent Sunday.
      chopLimit = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay());
    } else if (this.data.bucketSize === 'month') {
      // Get the first of the current month.
      chopLimit = new Date(now.getFullYear(), now.getMonth(), 1);
    } else {
      // Get midnight of today (ie, the boundary between today and yesterday)
      chopLimit = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }
    bucketed = _.filter(bucketed, function (datum) {
      return datum.date < chopLimit / 1000;
    });

    this.data.series = this.makeSeries(bucketed, this.data.seriesSpec);

    // Scale data based on axis groups
    this.axisGroups = {};
    for (i = 0; i < this.data.series.length; i += 1) {
      series = this.data.series[i];
      name = series.axisGroup;
      if (this.axisGroups[name] === undefined) {
        this.axisGroups[name] = {
          max: -Infinity
        };
      }

      // Only adjust the axis max if the series is enabled.
      if (!series.disabled) {
        this.axisGroups[name].max = Math.max(this.axisGroups[name].max, series.max);
      }
    }

    function mapHandler(point) {
      return {
        x: point.x,
        y: point.y / axisGroup.max
      };
    }

    for (i = 0; i < this.data.series.length; i += 1) {
      series = this.data.series[i];
      axisGroup = this.axisGroups[series.axisGroup];
      series.data = _.map(series.data, mapHandler);
      series.scale = axisGroup.max;
      axis = this.d3.axises[series.axisGroup];
      if (axis) {
        axis.setScale(axisGroup.max);
      }
    }
  };

  window.k.Graph = Graph;

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
  Graph.prototype.makeSeries = function (objects, descriptors) {
    var i;
    var series = [];
    var desc;
    var min, max, data;
    var windowMin, windowMax;
    var stroke, fill;
    var r, g, b;
    var palette = new Rickshaw.Color.Palette();

    if (this.rickshaw.graph) {
      windowMin = this.rickshaw.graph.window.xMin || -Infinity;
      windowMax = this.rickshaw.graph.window.xMax || +Infinity;
    } else {
      windowMin = -Infinity;
      windowMax = +Infinity;
    }

    function mapHandler(datum) {
      var val = desc.func(datum);

      if (isNaN(val) ) {
        val = 0;
      }

      if (windowMin <= datum.date && datum.date <= windowMax) {
        min = Math.min(min, val);
        max = Math.max(max, val);
      }

      return {x: datum.date, y: val};
    }

    function yFormatter(value) {
      return Math.floor(value * 100) + '%';
    }

    for (i = 0; i < descriptors.length; i += 1) {
      min = Infinity;
      max = -Infinity;
      desc = descriptors[i];

      data = _.map(objects, mapHandler);

      if (max <= 0 || isNaN(max) || !isFinite(max)) {
        max = 1;
      }

      if (this.graph.renderer === 'area') {
        stroke = desc.color || palette.color(desc.name);
        if (desc.area) {
          r = parseInt(desc.color.slice(1, 3), 16);
          g = parseInt(desc.color.slice(3, 5), 16);
          b = parseInt(desc.color.slice(5, 7), 16);
          fill = interpolate('rgba(%s,%s,%s,0.5)', [r, g, b]);
        } else {
          fill = 'rgba(0, 0, 0, 0.0)';
        }
      } else {
        // This is a bar graph. 'fill' is really color.
        stroke = undefined;
        fill = desc.color;
      }

      series[i] = {
        name: desc.name,
        slug: desc.slug,
        disabled: desc.disabled || false,
        type: desc.type || 'value',

        stroke: stroke,
        color: fill,
        axisGroup: desc.axisGroup,
        min: min,
        max: max,
        data: data
      };

      if (series[i].type === 'percent') {
        series[i].yFormatter = yFormatter;
      }
    }

    // Rickshaw gets angry when its data isn't sorted.
    function sortCallback (v1, v2) {
      return v1.x - v2.x;
    }

    for (i = 0; i < descriptors.length; i += 1) {
      series[i].data.sort(sortCallback);
    }

    return series;
  };

  Graph.prototype.getGraphData = function () {
    var palette = new Rickshaw.Color.Palette();
    var series = new Rickshaw.Series(this.data.series, palette);

    series.active = function () {
      // filter by active.
      return $.map(this, function (s) {
        if (!s.disabled) {
          return s;
        }
      });
    };

    return series;
  };

  Graph.prototype.initBucketUI = function () {
    if (!this.options.bucket) { return; }

    var i;
    var bucketSizes = [
      {value: 'day', text: gettext('Daily')},
      {value: 'week', text: gettext('Weekly')},
      {value: 'month', text: gettext('Monthly')}
    ];

    var $bucket = $('<div class="bucket"></div>')
      .appendTo(this.dom.elem.find('.inline-controls'));
    var $select = $('<select>');

    for (i = 0; i < bucketSizes.length; i += 1) {
      $('<option name="bucketing">')
        .val(bucketSizes[i].value)
        .text(bucketSizes[i].text)
        .appendTo($select);
    }
    $bucket.append($select);

    var self = this;
    $select.on('change', function () {
      self.data.bucketSize = $(this).val();
      self.rebucket();
      self.update();
    });
  };

  Graph.prototype._xFormatter = function (seconds) {
    var sizes = {};
    sizes.week = gettext('Week beginning %(year)s-%(month)s-%(date)s');
    sizes.month = gettext('Month beginning %(year)s-%(month)s-%(date)s');

    var key = this.data.bucketSize;
    var format = sizes[key];
    if (format === undefined) {
      format = '%(year)s-%(month)s-%(date)s';
    }

    return k.dateFormat(format, new Date(seconds * 1000));
  };

  Graph.prototype.initGraph = function () {
    var HoverClass;
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
        yFormatter: Math.floor,
        graph: this.rickshaw.graph
      }, this.hover);

      if (this.graph.renderer === 'bar') {
        HoverClass = Rickshaw.Graph.ScaledBarHoverDetail;
      } else {
        HoverClass = Rickshaw.Graph.KHover;
      }

      this.rickshaw.hover = new HoverClass(hoverOpts);
    }

    // :(
    Graph.monkeyPatch(this.rickshaw.graph);

    this.toRender.push(this.rickshaw.graph);
  };

  Graph.prototype.initSlider = function () {
    var self = this;
    var minDate;

    if (this.options.slider) {
      this.dom.slider = this.dom.elem.find('.slider');
      this.dom.slider.empty();

      var slider = new Rickshaw.Graph.RangeSlider({
        graph: this.rickshaw.graph,
        element: this.dom.slider
      });

      this.slider = slider.element;

      // About 6 months ago, as epoch seconds.
      minDate = (+new Date() - (1000 * 60 * 60 * 24 * 180)) / 1000;
      this.rickshaw.graph.window.xMin = minDate;

      this.rebucket();
      this.update();

      this.slider.slider('values', 0, minDate);
      this.slider.on('slide', function() {
        self.rebucket();
        self.update();
      });
    }
  };

  Graph.prototype.initDateRange = function () {
    var self = this, i;
    var now, ytd_ago, all_ago;
    var $inlines, $presets;
    var DAY = 24 * 60 * 60;
    var label_html;

    now = new Date();
    ytd_ago = (now - new Date(now.getFullYear(), 0, 0)) / 1000;
    all_ago = ((now / 1000) - this.data.series[0].data[0].x);

    var presets = [
      [30 * DAY, gettext('1m', 'Short for 1 month')],
      [90 * DAY, gettext('3m', 'Short for 3 months')],
      [180 * DAY, gettext('6m', 'Short for 6 months')],
      [ytd_ago, gettext('YTD', 'Short "Year to Date"')],
      [365 * DAY, gettext('1y', 'Short for 1 year')],
      [all_ago, gettext('All')]
    ];

    if (this.options.daterange) {
      label_html = interpolate(gettext('From %(from_input)s to %(to_input)s'), {
        from_input: '<input type="date" name="start" />',
        to_input: '<input type="date" name="end" />'
      }, true);

      $inlines = this.dom.elem.find('.inline-controls');
      var $label = $('<span/>')
        .html(label_html)
        .appendTo($('<div class="range"/>').appendTo($inlines));
      $presets = $('<div class="range-presets"/>').appendTo($inlines);

      $label.find('input[type=date]').datepicker({
        dateFormat: 'yy-mm-dd'
      });

      $label.on('change', 'input', function () {
        var $this = $(this);
        var val = $this.val();
        if ($this.prop('name') === 'start') {
          self.setRange(val, undefined);
        } else {
          self.setRange(undefined, val);
        }
      });

      this.rickshaw.graph.onUpdate(function () {
        var window = self.rickshaw.graph.window;

        now = +new Date() / 1000;
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

      var clickHandler = function() {
        now = +new Date() / 1000;
        var min = (now - $(this).data('days-ago'));

        self.rickshaw.graph.window.xMin = min;
        self.rickshaw.graph.window.xMax = undefined;
        if (self.options.slider) {
          self.slider.slider('values', [min, now]);
        }

        self.rebucket();
        self.update();
      };

      for (i = 0; i < presets.length; i += 1) {
        $('<button />')
          .data('days-ago', presets[i][0])
          .text(presets[i][1])
          .appendTo($presets)
          .on('click', clickHandler);
      }
    }
  };

  Graph.prototype.initAxises = function () {
    var axis, key, opts, i;
    this.d3.axises = {};

    if (this.options.xAxis) {
      new Rickshaw.Graph.Axis.Time({ // eslint-disable-line
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
      var SIDES = ['left', 'right'];

      for (key in this.axisGroups) {
        if (this.axisGroups.hasOwnProperty(key)) {
          i += 1;
          opts.scale = this.axisGroups[key].max;
          opts.side = SIDES[i];
          axis = new Rickshaw.Graph.Axis.ScaledY(opts);
          this.toRender.push(axis);
          this.d3.axises[key] = axis;
        }
      }
    }
  };

  Graph.prototype.initLegend = function () {
    if (this.options.legend === 'mini') {

      var i;
      var line;
      var $legend, $series, $li;

      $legend = $('<div class="legend"></div>')
        .appendTo(this.dom.elem.find('.inline-controls'));
      $series = $('<ul>');

      for (i = 0; i < this.data.series.length; i += 1) {
        line = this.data.series[i];
        $li = $('<li>')
          .toggleClass('disabled', line.disabled)
          .data('line', line)
          .data('line-index', i)
          .appendTo($series);
        $('<span/>')
          .addClass('color-square')
          .css('border-color', line.stroke || line.color)
          .appendTo($li);
        $('<span>').text(line.name).appendTo($li);
      }

      $legend.on('click', 'li', function (ev) {
        var $elem = $(ev.currentTarget);

        if ($elem.siblings(':not(.disabled)').length === 0) {
          return;
        }

        line = $elem.data('line');
        var index = $elem.data('line-index');

        line.disabled = !line.disabled;
        $elem.toggleClass('disabled', line.disabled);
        this.data.seriesSpec[index].disabled = line.disabled;

        this.rebucket();
        this.update();
      }.bind(this));

      $legend.append($series);

    } else if (this.options.legend) {

      this.dom.legend = this.dom.elem.find('.legend');
      this.dom.legend.empty();

      this.rickshaw.legend = new Rickshaw.Graph.Legend( {
        graph: this.rickshaw.graph,
        element: this.dom.legend[0] // legend can't handle jQuery objects
      });

      new Rickshaw.Graph.Behavior.Series.Toggle({ // eslint-disable-line
        graph: this.rickshaw.graph,
        legend: this.rickshaw.legend
      });

      new Rickshaw.Graph.Behavior.Series.Order({ // eslint-disable-line
        graph: this.rickshaw.graph,
        legend: this.rickshaw.legend
      });
    }
  };

  Graph.prototype.initTimeline = function () {
    var $timeline, timeline;
    var i, j;
    var annot;

    if (this.options.timeline) {
      this.dom.timelines = this.dom.elem.find('.timelines');
      var $timelines = $(this.dom.timelines);
      this.rickshaw.timelines = [];

      for (i = 0; i < this.data.annotations.length; i += 1) {
        annot = this.data.annotations[i];
        $timeline = $('<div class="timeline"/>').appendTo($timelines);

        timeline = new Rickshaw.Graph.Annotate({
          'graph': this.rickshaw.graph,
          'element': $timeline[0]
        });

        for (j = 0; j < annot.data.length; j += 1) {
          timeline.add(annot.data[j].x, annot.data[j].text);
        }

        this.rickshaw.timelines.push(timeline);
      }
    }
  };

  Graph.prototype.initSets = function () {
    if (!this.options.sets) { return; }

    var key;
    var $sets = $('<div class="sets"></div>');

    for (key in this.metadata.sets) {
      if (this.metadata.sets.hasOwnProperty(key)) {
        $('<input type="checkbox" name="sets"/>').val(key).appendTo($sets);
        $('<label for="sets">').text(key).appendTo($sets);
      }
    }

    var self = this;
    $sets.on('change', 'input[name=sets]', function () {
      var count = 0;
      $sets.find('input[name=sets]').each(function () {
        count += !!$(this).prop('checked');
      });
      if (count === 0) {
        $(this).prop('checked', true);
        return;
      }

      var $this = $(this);
      var _set = self.metadata.sets[$this.attr('value')];
      var disabled = !$this.prop('checked');
      var i;
      var line;

      for (i = 0; i < self.data.series.length; i += 1) {
        line = self.data.series[i];
        if (_set.indexOf(line.slug) !== -1) {
          line.disabled = disabled;
          self.data.seriesSpec[i].disabled = disabled;
        }
      }

      self.update();
    });

    this.dom.elem.find('.inline-controls').append($sets);
    $sets.find('input[name=sets]').prop('checked', true);
  };

  Graph.prototype.render = function () {
    var i;

    for (i = 0; i < this.toRender.length; i += 1) {
      this.toRender[i].render();
    }

    if (this.options.yAxis) {
      this.dom.yAxis.css({'top': this.dom.graph.position().top});
    }
  };

  Graph.prototype.update = function () {
    this.rickshaw.graph.series = this.getGraphData();
    this.rickshaw.graph.stackedData = null;
    this.rickshaw.graph.update();
  };

  /* Accepts start and end as one of:
   *  - Seconds since epoch
   *  - Date objects
   *  - Strings formatted as YYYY-MM-DD
   */
  Graph.prototype.setRange = function (start, end) {
    var window = this.rickshaw.graph.window;

    if (start === undefined) {
      start = window.xMin;
    }
    if (end === undefined) {
      end = window.xMax;
    }

    start = Graph.toSeconds(start);
    end = Graph.toSeconds(end);

    window.xMin = start;
    window.xMax = end;
    this.rebucket();
    this.update();
  };
  /* end Graph */

  /* These are datum transforming methods. They take an object like
   * {created: 1367270055, foo: 10, bar: 20, baz: 30} and return a number.
   */

  // Returns the value associated with a key.
  // identity('foo') -> 10
  Graph.identity = function (key) {
    return function (d) {
      return d[key];
    };
  };

  // Divides the first key by the second.
  // fraction('foo', 'bar') -> 0.5
  Graph.fraction = function (topKey, bottomKey) {
    return function (d) {
      return d[topKey] / d[bottomKey];
    };
  };

  // Subtract the second key from the first.
  // difference('foo', 'bar')({foo: 5, bar: 2}) -> 3
  Graph.difference = function (leftKey, rightKey) {
    return function(d) {
      return d[leftKey] - d[rightKey];
    };
  };

  // Takes a date in one of the followign formats and returns seconds
  // since the epoch: Date objects, strings in the format 'YYYY-MM-DD',
  // Integers in second since the epoch form..
  Graph.toSeconds = function (obj) {
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
  };

  /* Takes two or more arguments. The arguments are the keys that
   * represent an entire collection (all pieces in a pie). The first key
   * is the current slice of the pie. Returns what percent the first key
   * is of the total, as a decimal between 0.0 and 1.0.
   *
   * percentage('foo', 'bar', 'baz') -> 10 / (10 + 20 + 30) = ~0.166
   */
  Graph.percentage = function (partKey /* *restKeys */) {
    var allKeys = Array.prototype.slice.call(arguments);
    return function (d) {
      var sum = 0;
      _.each(allKeys, function (key) {
        sum += d[key];
      });
      return d[partKey] / sum;
    };
  };


  // Monkey Patches. Agh!
  Graph.monkeyPatch = function (graph) {

    // The bar render's _frequentInterval function normally replaces itself
    // after the first call as a way of memoization. Unfortunatly this
    // prevents it from reacting to future data updates (like rebucketing).
    // This is a problem. The version removes the memoization bit, and makes
    // the frequentInterval always include a magnitude value.
    if (graph.renderer._frequentInterval) {
      graph.renderer._frequentInterval = function () {
        var stackedData = this.graph.stackedData || this.graph.stackData();
        var data = stackedData.slice(-1).shift();

        var intervalCounts = {};
        var i;
        var interval;

        for (i = 0; i < data.length - 1; i += 1) {
          interval = data[i + 1].x - data[i].x;
          intervalCounts[interval] = intervalCounts[interval] || 0;
          intervalCounts[interval] += 1;
        }

        // The magnitude key in this object was added in the monkey patch.
        var frequentInterval = { count: 0, magnitude: 1 };

        Rickshaw.keys(intervalCounts).forEach(function (j) {
          if (frequentInterval.count < intervalCounts[j]) {

            frequentInterval = {
              count: intervalCounts[j],
              magnitude: j
            };
          }
        } );

        // This is the line the monkey patch rips out.
        // this._frequentInterval = function () { return frequentInterval };

        return frequentInterval;
      };
    }
  };


  /* This is a mostly intact version of Rickshaw.Graph.HoverDetail that
   * is modified to work with scaled series, and to work better with bar
   * charts.
   *
   * The `render` method has changed to call a method to determine the
   * location of the tooltip, and to respect series scale (`series.scale`).
   *
   * The location of the tooltip is in the middle of the bar drawn by the
   * bar renderer, and the selection is based on the visible rectangles.
   */

  Rickshaw.namespace('Rickshaw.Graph.ScaledBarHoverDetail');
  Rickshaw.Graph.ScaledBarHoverDetail = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {

    getHoverPoint: function (point) {
      var barWidth = this.graph.renderer.barWidth();
      var x = this.graph.x(point.value.x);
      if (this.graph.renderer.unstack) {
        barWidth /= this.graph.series.active().length;
        x += barWidth * (point.order - 1);
      }
      return {
        left: x + barWidth / 2,
        top: this.graph.y(point.value.y0 + point.value.y / 2)
      };
    },

    render: function (args) {
      var points = args.points;
      var point = points.filter( function (p) { return p.active; } ).shift();

      if (!point || point.value.y === null) { return; }

      var xFormatter = point.series.xFormatter || this.xFormatter;
      var yFormatter = point.series.yFormatter || this.yFormatter;

      var scaledY = point.value.y * (point.series.scale || 1);
      var formattedXValue = xFormatter(point.value.x);
      var formattedYValue = yFormatter(scaledY);

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

      if (typeof this.onRender === 'function') {
        this.onRender(args);
      }
    },

    update: function (e) {

      e = e || this.lastEvent;
      if (!e) { return; }
      this.lastEvent = e;

      if (!e.target.nodeName.match(/^(path|svg|rect)$/)) { return; }

      var active = this.graph.series.active();
      var graph = this.graph;
      var barWidth = graph.renderer.barWidth() + graph.renderer.gapSize;

      if (graph.renderer.unstack) {
        barWidth = graph.renderer.barWidth() / active.length;
      }

      var eventX = e.offsetX || e.layerX;
      var eventY = e.offsetY || e.layerY;

      var i, j, k;
      var points = [];
      var nearestPoint;

      // Iterate through each series, and find the point that most closely
      // matches the mouse pointer.

      var series, data, domainX, domainIndexScale, approximateIndex, dataIndex;
      var value, barOffset, left, right, bottom, top, point;

      for (i = 0; i < active.length; i += 1) {
        series = active[i];

        data = this.graph.stackedData[i];
        domainX = graph.x.invert(eventX);

        domainIndexScale = d3.scale.linear()
          .domain([data[0].x, data.slice(-1)[0].x])
          .range([0, data.length - 1]);

        approximateIndex = Math.round(domainIndexScale(domainX));
        dataIndex = Math.min(approximateIndex || 0, data.length - 1);

        k = approximateIndex;
        while (k < data.length - 1) {

          if (!data[k] || !data[k + 1]) { break; }

          if (data[k].x <= domainX && data[k + 1].x > domainX) {
            dataIndex = k;
            break;
          }

          if (data[k + 1].x <= domainX) { k += 1; } else { k -= 1; }
        }

        if (dataIndex < 0) { dataIndex = 0; }
        value = data[dataIndex];

        barOffset = graph.renderer.unstack ? i * barWidth : 0;

        left = graph.x(value.x) + barOffset;
        right = left + barWidth;
        bottom = graph.y(value.y0);
        top = graph.y(value.y + value.y0);

        point = {
          series: series,
          value: value,
          order: i,
          name: series.name
        };

        if (left <= eventX && eventX < right &&
          top <= eventY && eventY < bottom) {

          nearestPoint = point;
        }

        points.push(point);
      }

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
    }
  });


  Rickshaw.namespace('Rickshaw.Graph.Axis');

  Rickshaw.Graph.Axis.ScaledY = function (args) {
    this.graph = args.graph;
    this.side = args.side || 'left';
    this.scale = args.scale || 1.0;
    this.tickFormat = args.tickFormat || function (v) { return v; };

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
        .css('margin-right', '10px');
    }

    var oldWidth = $(this.graph.element).outerWidth();
    this.graph.setSize({width: oldWidth - $axis.outerWidth()});

    $axis.css('height', $(this.graph.element).innerHeight());

    this.element = $axis[0];
    this.graph.onUpdate(this.render);
  };

  Rickshaw.Graph.Axis.ScaledY.prototype.render = function () {
    // TODO: Figure out why `this` does not always exist within the scope of
    // this function.
    if (this) {
      var w = $(this.element).innerWidth();
      var h = $(this.element).innerHeight();
      var scale, axis, svg, group;

      d3.select(this.element).select('*').remove();

      var padding = 10;
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
    }
  };

  Rickshaw.Graph.Axis.ScaledY.prototype.setScale = function (s) {
    this.scale = s || 1.0;
    this.render();
  };


  /* Custom hover class for Graph.
   *
   * This will find all points in a vertical slice for the graph and show
   * them in a single dialog.
   */
  Rickshaw.namespace('Rickshaw.Graph.KHover');

  Rickshaw.Graph.KHover = Rickshaw.Class.create({

    initialize: function (args) {

      var graph = args.graph;
      this.graph = graph;

      this.xFormatter = args.xFormatter || function (x) {
        return new Date( x * 1000 ).toUTCString();
      };

      this.yFormatter = args.yFormatter || function (y) {
        return y === null ? y : y.toFixed(2);
      };

      var element = document.createElement('div');
      this.element = element;
      element.className = 'khover';

      this.visible = true;
      graph.element.appendChild(element);

      this.lastEvent = null;
      this._addListeners();
    },

    /* Called when the mouse moves. Collects a set of points to draw, and
     * then calls this.render if appropriate. */
    update: function (e) {

      e = e || this.lastEvent;
      if (!e) { return; }
      this.lastEvent = e;

      if (!e.target.nodeName.match(/^(path|svg|rect)$/)) { return; }

      var i;
      var graph = this.graph;

      var eventX = e.offsetX || e.layerX;
      var eventY = e.offsetY || e.layerY;

      var points = [];
      var data = this.graph.stackedData[0];

      // The x value in the units of the graph that corresponds to the pointer.
      var domainX = graph.x.invert(eventX);
      var xMin = graph.window.xMin || data[0].x;
      var xMax = graph.window.xMax || data.slice(-1)[0].x;
      var domainIndexScale = d3.scale.linear()
        .domain([xMin, xMax])
        .range([0, data.length - 1]);

      var dataIndex = Math.round(domainIndexScale(domainX)) || 0;
      // clamp dataIndex between 0 and length;
      dataIndex = Math.max(0, Math.min(dataIndex, data.length - 1));

      // Sometimes the data has holes in it. In that case, the dataIndex
      // will be wrong. Walk around the graph until we are at about the
      // right point.
      while (dataIndex >= 0 && dataIndex < data.length - 1) {
        if (data[dataIndex].x <= domainX && domainX <= data[dataIndex + 1].x) {
          // the right one.
          break;
        }

        // Move to the left or right, as appropratiate.
        if (data[dataIndex].x > domainX) { dataIndex -= 1; } else { dataIndex += 1; }
      }

      // Choose the closer of the two points.
      if (data[dataIndex + 1] &&
        data[dataIndex + 1].x - domainX < domainX - data[dataIndex].x) {
        dataIndex += 1;
      }

      var activeSeries = graph.series.active();

      for (i = 0; i < graph.stackedData.length; i += 1) {
        points.push({
          x: graph.stackedData[i][dataIndex].x,
          y: graph.stackedData[i][dataIndex].y,
          series: activeSeries[i]
        });
      }

      if (this.visible) {
        this.render({
          eventX: eventX,
          eventY: eventY,
          x: points[0].x,
          points: points
        });
      }
    },

    hide: function () {
      this.visible = false;
      this.element.classList.add('inactive');
    },

    show: function () {
      this.visible = true;
      this.element.classList.remove('inactive');
    },

    /* Create dom elements to render the element. Usually called after
     * `this.update` noticed the mouse move. */
    render: function (args) {
      var i, val, x, labelBounds, graphBounds;
      var formatter = this.xFormatter;
      var point, series;
      var dot, li, label = document.createElement('ul');
      var transform;

      this.element.innerHTML = '';

      li = document.createElement('li');
      li.className = 'date';
      li.innerHTML = formatter(args.x);
      label.appendChild(li);

      for (i = 0; i < args.points.length; i += 1) {
        point = args.points[i];
        series = point.series;
        formatter = series.yFormatter || this.yFormatter;
        li = document.createElement('li');
        val = point.y * series.scale;

        li.innerHTML = interpolate('<span class="color" style="background-color: %s;"></span>%s: %s',
          [series.stroke, series.name, formatter(val)]);
        label.appendChild(li);

        dot = document.createElement('div');
        dot.className = 'dot';

        transform = interpolate('translate(0, %spx)', [this.graph.y(point.y)]);
        dot.style.transform = transform;
        dot.style['-webkit-transform'] = transform;
        dot.style.borderColor = series.stroke;
        this.element.appendChild(dot);
      }

      this.element.appendChild(label);

      labelBounds = label.getBoundingClientRect();
      graphBounds = this.graph.element.getBoundingClientRect();

      // To be honest, I don't know why *2 and -20. But they work nicely
      // across the graphs I tried.
      var rightMin = graphBounds.right - labelBounds.width * 2;
      if (args.eventX > rightMin) {
        x = this.graph.x(point.x) - labelBounds.width - 20;
        this.element.className = 'khover right';
      } else {
        x = this.graph.x(point.x);
        this.element.className = 'khover';
      }

      // Really, webkit? Really?
      transform = interpolate('translate(%spx, 0)', [x]);
      this.element.style.transform = transform;
      this.element.style['-webkit-transform'] = transform;

      this.show();
    },

    _addListeners: function () {

      this.graph.element.addEventListener(
        'mousemove',
        function (e) {
          this.visible = true;
          this.update(e);
        }.bind(this),
        false
      );

      this.graph.onUpdate( function () { this.update(); }.bind(this) );

      this.graph.element.addEventListener(
        'mouseout',
        function (e) {
          if (e.relatedTarget && !(e.relatedTarget.compareDocumentPosition(this.graph.element) & Node.DOCUMENT_POSITION_CONTAINS)) {
            this.hide();
          }
        }.bind(this),
        false
      );
    }
  });

})();
