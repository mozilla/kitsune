/* globals d3:false, $:false, _:false */
/* jshint esnext: true */

export default class Chart {
  constructor($container, options) {
    let defaults = {
      chartColors: ['#EE2820', '#F25743', '#F58667', '#F9B58B', '#FDE4AF', '#E3F1B6', '#AADA9F', '#72C489', '#39AD72', '#00975C'],
      axes: {
        xAxis: {
          labels: [],
          labelOffsets: { x: 15, y: 23 }
        },
        yAxis: {
          labels: [],
          labelOffsets: { x: 5, y: 23 }
        },
        getPosition: (position, axis, index) => {
          let gridSize = (position === 'y') ? this.gridSize/2 : this.gridSize;

          if (position === axis[0]) {
            return index * gridSize;
          } else {
            return -gridSize;
          }
        }
      },
      margin: { top: 40, right: 0, bottom: 100, left: 75 },
      width: 860,
      height: 430,
      grid: { rows: 12, columns: 12 },
      gridSize: 71,
      buckets: 10,
      legendElementWidth: 95,
      data: [],
      dom: {
        graphContainer: $container.find('.graph').get()[0]
      }
    };

    $.extend(true, this, defaults, options);

    this.init();
  }

  // Render whatever pieces of the chart we can while waiting for data
  preRender() {
    // draw the container svg for the chart
    this.dom.svg = d3.select(this.dom.graphContainer).append('svg')
      .attr('width', this.width + this.margin.left + this.margin.right)
      .attr('height', this.height + this.margin.top + this.margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');

    this.dom.svg.append('g')
      .attr('class', 'data');

    this.setupAxis('xAxis');
    this.setupLegend();
  }

  setupAxis(axis) {
    let self = this;
    let axisGroup = self.dom.svg.append('g')
      .attr('class', axis);

    axisGroup.selectAll()
      .data(self.axes[axis].labels)
        .enter().append('text')
        .text(function(d,i) { return d; })
        .attr('x', function(d, i) {
          return self.axes.getPosition('x', axis, i) + self.axes[axis].labelOffsets.x;
        })
        .attr('y', function(d, i) {
          return self.axes.getPosition('y', axis, i) + self.axes[axis].labelOffsets.y;
        })
  }

  setupLegend() {
    let self = this;
    let legendData = self.chartColors;
    let legendYPosition = (self.grid.rows * self.gridSize/2) + self.gridSize;
    let legendXPositions = i => {
      return (self.legendElementWidth * i) - self.gridSize;
    }

    let legend = self.dom.svg.append('g')
      .attr('class', 'legend');

    legend.selectAll('rect')
      .data(legendData, function(d) { return d; })
        .enter().append('rect')
        .attr('x', function(d, i) { return legendXPositions(i); })
        .attr('y', legendYPosition)
        .attr('width', self.legendElementWidth)
        .attr('height', self.gridSize / 3.6)
        .style('fill', function(d, i) { return self.chartColors[i]; });

    legend.selectAll('text')
      .data(legendData, function(d) { return d; })
        .enter().append('text')
        .text(function(d, i) { return '≥ ' + Math.round(i / self.buckets * 100) + '%'; })
        .attr('x', function(d, i) { return legendXPositions(i) + 7; })
        .attr('y', legendYPosition + 14);
  }

  init() {
    this.preRender();
  }

  setupGrid(filteredData, filter) {
    let self = this;
    let kindFilter = filter;

    self.dom.cohorts = self.dom.svg.select('.data').selectAll('g')
      .data(filteredData);

    self.dom.cohorts.enter().append('g');

    self.dom.cohorts
      .attr('width', self.width)
      .attr('height', self.gridSize/2)
      .attr('x', 0)
      .attr('y', function(d, i) {
        return i * self.gridSize/2;
      })
      .attr('class', function(d, i) {
        return 'cohort-group ' + kindFilter;
      });

    self.dom.cohorts.exit().remove();
  }

  populateData(filter) {
    let self = this;
    let kindFilter = filter;
    let filteredData = _.filter(self.data, function(datum, index) {
      return datum.kind === kindFilter;
    });

    self.setupGrid(filteredData, kindFilter);

    self.dom.cohorts.each(function(cohort, i) {
      let cohortGroupNumber = i;
      let cohortOriginalSize = cohort.size;
      let coloredBoxes = d3.select(this).selectAll('rect')
        .data(cohort.retention_metrics);

      coloredBoxes.enter().append('rect');

      coloredBoxes
        .attr('class', 'retention-week')
        .attr('height', self.gridSize/2)
        .attr('width', self.gridSize)
        .attr('x', function(d, i) { return i * self.gridSize; })
        .attr('y', function(d, i) { return cohortGroupNumber * self.gridSize/2; })
        .style('fill', function(d) {
          return self.colorScale(Math.floor((d.size / cohortOriginalSize) * 100) || 0);
        })
        .style('stroke', '#000')
        .style('stroke-opacity', 0.05)
        .style('stroke-width', 1);

      coloredBoxes.exit().remove();

      let sizeText = d3.select(this).selectAll('text')
        .data(cohort.retention_metrics)

      sizeText.enter().append('text');

      sizeText
        .text(function(d, i) {
          let percentage = Math.floor((d.size / cohortOriginalSize) * 100) || 0;
          return d.size + ' (' + percentage + '%)';
        })
        .attr('x', function(d, i ) { return i * self.gridSize + 10; })
        .attr('y', function(d, i) { return (cohortGroupNumber * self.gridSize/2) + 23; });

      sizeText.exit().remove();

    });
  }
}
