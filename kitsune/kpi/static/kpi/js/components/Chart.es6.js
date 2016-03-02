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
      colorScale() {
        return d3.scale.quantize()
          .domain([0, 100])
          .range(this.chartColors)
      },
      margin: { top: 40, right: 0, bottom: 20, left: 75 },
      width: 860,
      height: 440,
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
        .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);

    this.dom.svg.append('g')
      .attr('class', 'data');

    this.setupAxis('xAxis');
    this.setupLegend();
  }

  setupAxis(axis) {
    let axisGroup = this.dom.svg.append('g')
      .attr('class', axis);

    axisGroup.selectAll()
      .data(this.axes[axis].labels)
        .enter().append('text')
        .text((d,i) => d)
        .attr('x', (d, i) => {
          return this.axes.getPosition('x', axis, i) + this.axes[axis].labelOffsets.x;
        })
        .attr('y', (d, i) => {
          return this.axes.getPosition('y', axis, i) + this.axes[axis].labelOffsets.y;
        })
  }

  setupLegend() {
    let legendData = this.chartColors;
    let legendYPosition = (this.grid.rows * this.gridSize/2 + 15);
    let legendXPositions = i => (this.legendElementWidth * i) - this.gridSize;

    let legend = this.dom.svg.append('g')
      .attr('class', 'legend');

    legend.selectAll('rect')
      .data(legendData, function(d) { return d; })
        .enter().append('rect')
        .attr('x', (d, i) => legendXPositions(i))
        .attr('y', legendYPosition)
        .attr('width', this.legendElementWidth)
        .attr('height', this.gridSize / 3.6)
        .style('fill', (d, i) => this.chartColors[i]);

    legend.selectAll('text')
      .data(legendData, function(d) { return d; })
        .enter().append('text')
        .text((d, i) => `≥${Math.round(i / this.buckets * 100)}%`)
        .attr('x', (d, i) => legendXPositions(i) + 7)
        .attr('y', legendYPosition + 14);
  }

  init() {
    this.preRender();
  }

  setupGrid(filteredData, filter) {
    let kindFilter = filter;

    this.dom.cohorts = this.dom.svg.select('.data').selectAll('g')
      .data(filteredData);

    this.dom.cohorts.enter().append('g');

    this.dom.cohorts
      .attr('width', this.width)
      .attr('height', this.gridSize/2)
      .attr('x', 0)
      .attr('y', (d, i) => i * this.gridSize / 2)
      .attr('class', `cohort-group ${kindFilter}`)
      .attr('id', (d, i) => `cohort-group-${i}`);

    this.dom.cohorts.exit().remove();
  }

  populateData(filter) {
    let self = this;
    let kindFilter = filter;
    let filteredData = _.filter(this.data, function(datum, index) {
      return datum.kind === kindFilter;
    });

    this.setupGrid(filteredData, kindFilter);

    this.dom.cohorts.each((cohort, i) => {
      let cohortGroupNumber = i;
      let cohortOriginalSize = cohort.size;
      let gSelection = d3.select('#cohort-group-' + i);

      let coloredBoxes = gSelection.selectAll('rect')
        .data(cohort.retention_metrics);

      let sizeText = gSelection.selectAll('text')
        .data(cohort.retention_metrics);

      coloredBoxes.enter().append('rect');

      coloredBoxes
        .attr('class', 'retention-week')
        .attr('height', this.gridSize/2)
        .attr('width', this.gridSize)
        .attr('x', (d, i) => i * this.gridSize)
        .attr('y', (d, i) => cohortGroupNumber * this.gridSize/2)
        .style('fill', (d) => {
          return this.colorScale()(Math.floor((d.size / cohortOriginalSize) * 100) || 0);
        })
        .style('stroke', '#000')
        .style('stroke-opacity', 0.05)
        .style('stroke-width', 1);

      coloredBoxes.exit().remove();

      sizeText.enter().append('text');

      sizeText
        .text(function(d, i) {
          let percentage = Math.floor((d.size / cohortOriginalSize) * 100) || 0;
          return `${d.size} (${percentage}%)`;
        })
        .attr('x', (d, i) => i * this.gridSize + 10)
        .attr('y', (d, i) => (cohortGroupNumber * this.gridSize/2) + 23);

      sizeText.exit().remove();

    });
  }
}
