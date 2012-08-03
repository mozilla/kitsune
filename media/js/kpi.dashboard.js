/*
 * KPI Dashboard backbonejs app.
 */

(function($){

"use strict";


/*
 * Models
 */
window.ChartModel = Backbone.Model.extend({
    initialize: function(models, options) {
        this.url = options.url;
    },
    url: function() {
        return this.url;
    }
});


/*
 * Views
 */
window.BasicChartView = Backbone.View.extend({
    tagName: 'section',
    className: 'graph',

    initialize: function() {
        _.bindAll(this, 'render');

        this.model.bind('change', this.render);

        this.chartOptions = {
            chart: {
                renderTo: this.el,
                defaultSeriesType: 'line',
                width: 800
            },
            credits: {
                enabled: false
            },
            yAxis: {
                min: 0,
                title: ''
            },
            xAxis: {
                type: 'datetime',
                tickInterval: 24 * 3600 * 1000 * 30,
                dateTimeLabelFormats: {
                    month: '%b'
                }
            },
            plotOptions: {
                series: {
                    cursor: 'pointer',
                    marker: {
                        lineWidth: 1
                    },
                    stickyTracking: true
                }
            },
            title: {
                text: this.options.title
            },
            tooltip: {
                style: {
                    width: 200
                },
                enabled: true,
                shared: true,
                yDecimals: 0
            }
        };

        if (this.options.percent) {
            this.chartOptions.yAxis.title = {
                text: '%'
            };
            this.chartOptions.tooltip.ySuffix = '%';
            this.chartOptions.tooltip.yDecimals = 1;
        }
    },

    addModel: function(model) {
        model.bind('change', this.render);
    },

    render: function(model) {
        var self = this,
            data = model && model.get('objects');

        if(data) {

            // Create the chart if we haven't yet.
            if (!self.chart) {
                self.chart = new Highcharts.Chart(self.chartOptions);
            }

            _.each(this.options.series, function(series) {
                var mapper = series.mapper,
                    seriesData;
                if (!mapper) {
                    mapper = function(o){
                        return {
                            x: Date.parse(o['date']),
                            y: o[series.numerator] / o[series.denominator] * 100
                        };
                    };
                }

                seriesData = _.map(data, mapper);
                seriesData.reverse();

                self.chart.addSeries({
                    data: seriesData,
                    name: series.name || model.name
                });
            });
        }

        return this;
    }
});

window.StockChartView = Backbone.View.extend({
    template: _.template($("#chart-template").html()),
    tagName: 'section',
    className: 'graph',

    events: {
        'change .grouping': 'changeGrouping'
    },

    initialize: function() {
        _.bindAll(this, 'render', 'changeGrouping');

        this.model.bind('change', this.render);

        this.chartOptions = {
            chart: {
                alignTicks: false,
                width: 800
            },
            title: {
                text: this.options.title
            },
            rangeSelector: {
                selected: 2,
                buttons: [{
                    type: 'month',
                    count: 1,
                    /* L10n: short for "1 month" */
                    text: gettext('1m')
                }, {
                    type: 'month',
                    count: 3,
                    /* L10n: short for "3 months" */
                    text: gettext('3m')
                }, {
                    type: 'month',
                    count: 6,
                    /* L10n: short for "6 months" */
                    text: gettext('6m')
                }, {
                    type: 'ytd',
                    /* L10n: short for "Year To Date" */
                    text: gettext('YTD')
                }, {
                    type: 'year',
                    count: 1,
                    /* L10n: short for "1 year" */
                    text: gettext('1y')
                }, {
                    type: 'all',
                    text: gettext('All')
                }],
                buttonTheme: {
                    width: null
                },
                inputStyle: {
                    fontSize: '10px'
                },
                inputBoxStyle: {
                    top: '65px'
                }
            },
            xAxis: {
                type: 'datetime',
                tickInterval: 24 * 3600 * 1000 * 30,
                dateTimeLabelFormats: {
                    month: '%b'
                }
            },
            yAxis: [{
                maxPadding: 0,
                min: 0,
                title: '%'
            }, {
                gridLineWidth: 0,
                endOnTick: false,
                maxPadding: 0,
                tickPositions: [0, 100, 300],
                opposite: true,
                min: 0
            }],
            tooltip: {
                style: {
                    width: 200
                },
                shared: true,
                pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b><br/>'
            },
            credits: {
                enabled: false
            },
            plotOptions: {
                series: {
                    cursor: 'pointer',
                    marker: {
                        lineWidth: 1
                    },
                    stickyTracking: true
                }
            },
            legend: {
                enabled: true,
                y: 30,
                verticalAlign: 'top'
            },
            series: []
        };

        if (this.options.percent) {
            this.chartOptions.yAxis[0].title = {
                text: '%'
            };
        }

        $(this.el).html(this.template());
    },

    render: function() {
        var self = this,
            data = this.model.get('objects');

        self.chartOptions.chart.renderTo = $(this.el).find('.placeholder')[0];
        self.chartOptions.series = [];

        if(data) {
            _.each(this.options.series, function(series) {
                var mapper = series.mapper,
                    seriesData, seriesConfig;
                if (!mapper) {
                    mapper = function(o){
                        return {
                            x: Date.parse(o['date']),
                            y: o[series.numerator] / o[series.denominator] * 100
                        };
                    };
                }

                seriesData = _.map(data, mapper);
                seriesData.reverse();

                seriesConfig = {
                    name: series.name,
                    type: series.type || 'line',
                    yAxis: series.yAxis || 0,
                    data: seriesData,
                    tooltip: series.tooltip
                }

                // Group the data into weeks or months?
                if (self.grouping === 'm') {
                    seriesConfig.dataGrouping = {
                        approximation: series.approximation || 'average',
                        forced: true,
                        units: [['month', [1]]]
                    };
                } else if (self.grouping === 'w') {
                    seriesConfig.dataGrouping = {
                        approximation: series.approximation || 'average',
                        forced: true,
                        units: [['week', [1]]]
                    };
                }

                self.chartOptions.series.push(seriesConfig);
            });
            self.chart = new Highcharts.StockChart(self.chartOptions);
        }
        return this;
    },

    changeGrouping: function() {
        this.grouping = $(this.el).find('.grouping').val();
        this.render();
    }
});


/*
 * Application
 */
window.KpiDashboard = Backbone.View.extend({
    initialize: function() {
        // Create the models.
        this.questionsChart = new ChartModel([], {
            url: $(this.el).data('questions-url')
        });

        this.voteChart = new ChartModel([], {
            url: $(this.el).data('vote-url')
        });

        this.activeContributorsChart = new ChartModel([], {
            url: $(this.el).data('active-contributors-url')
        });

        this.elasticCtrChart = new ChartModel([], {
            url: $(this.el).data('elastic-ctr-url')
        });
        this.elasticCtrChart.name = 'Elastic';

        this.visitorsChart = new ChartModel([], {
            url: $(this.el).data('visitors-url')
        });

        this.l10nChart = new ChartModel([], {
            url: $(this.el).data('l10n-coverage-url')
        });

        // Create the views.
        this.questionsView = new StockChartView({
            model: this.questionsChart,
            title: gettext('Questions'),
            percent: true,
            series: [{
                name: gettext('Questions'),
                type: 'area',
                yAxis: 1,
                approximation: 'sum',
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['questions']
                    }
                }
            }, {
                name: gettext('Solved'),
                numerator: 'solved',
                denominator: 'questions',
                tooltip: {
                    ySuffix: '%',
                    yDecimals: 1
                }
            }, {
                name: gettext('Responded in 72 hours'),
                numerator: 'responded',
                denominator: 'questions',
                tooltip: {
                    ySuffix: '%',
                    yDecimals: 1
                }
            }]
        });

        this.voteChartView = new StockChartView({
            model: this.voteChart,
            title: gettext('Helpful Votes'),
            percent: true,
            series: [{
                name: gettext('Article Votes: % Helpful'),
                numerator: 'kb_helpful',
                denominator: 'kb_votes',
                tooltip: {
                  ySuffix: '%',
                  yDecimals: 1
                }
            }, {
                name: gettext('Answer Votes: % Helpful'),
                numerator: 'ans_helpful',
                denominator: 'ans_votes',
                tooltip: {
                  ySuffix: '%',
                  yDecimals: 1
                }
            }/* TODO: Leave this out for now, it overlaps the article votes.
            , {
                name: 'Total Votes: % Helpful',
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: (o['ans_helpful'] + o['kb_helpful']) / (o['kb_votes'] + o['ans_votes']) * 100
                    };
                }
            }*/]
        });

        this.activeContributorsView = new StockChartView({
            model: this.activeContributorsChart,
            title: gettext('Active Contributors'),
            series: [{
                name: gettext('en-US KB'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['en_us']
                    };
                }
            }, {
                name: gettext('non en-US KB'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['non_en_us']
                    };
                }
            }, {
                name: gettext('Support Forum'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['support_forum']
                    };
                }
            }, {
                name: gettext('Army of Awesome'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['aoa']
                    };
                }
            }]
        });

        this.ctrView = new BasicChartView({
            model: this.elasticCtrChart,
            title: gettext('Search Clickthrough Rate'),
            percent: true,
            series: [{
                mapper: function(o) {
                    return {
                        x: Date.parse(o['start']),
                        y: o['clicks'] / o['searches'] * 100
                    };
                }
            }]
        });

        this.visitorsView = new StockChartView({
            model: this.visitorsChart,
            title: gettext('Visitors'),
            series: [{
                name: gettext('Daily Unique Visitors'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['visitors']
                    };
                },
                tooltip: {
                    yDecimals: 0
                }
            }]
        });

        this.l10nView = new BasicChartView({
            model: this.l10nChart,
            title: gettext('L10n Coverage'),
            percent: true,
            series: [{
                name: gettext('L10n Coverage'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['coverage']
                    };
                }
            }]
        });

        // Render the views.
        $(this.el)
            .append(this.questionsView.render().el)
            .append($('#kpi-legend-questions'))
            .append(this.voteChartView.render().el)
            .append($('#kpi-legend-vote'))
            .append(this.activeContributorsView.render().el)
            .append($('#kpi-legend-active-contributors'))
            .append(this.ctrView.render().el)
            .append($('#kpi-legend-ctr'))
            .append(this.visitorsView.render().el)
            .append(this.l10nView.render().el)
            .append($('#kpi-legend-l10n'));


        // Load up the models.
        this.questionsChart.fetch();
        this.activeContributorsChart.fetch();
        this.voteChart.fetch();
        this.elasticCtrChart.fetch();
        this.visitorsChart.fetch();
        this.l10nChart.fetch();
    }
});


// Set Highcharts options.
Highcharts.setOptions({
    lang: {
        months: [gettext('January'),
                 gettext('February'),
                 gettext('March'),
                 gettext('April'),
                 gettext('May'),
                 gettext('June'),
                 gettext('July'),
                 gettext('August'),
                 gettext('September'),
                 gettext('October'),
                 gettext('November'),
                 gettext('December')],
        weekdays: [gettext('Sunday'),
                   gettext('Monday'),
                   gettext('Tuesday'),
                   gettext('Wednesday'),
                   gettext('Thursday'),
                   gettext('Friday'),
                   gettext('Saturday')],
        /* L10n: short for the individual months */
        shortMonths: [gettext('Jan'),
                      gettext('Feb'),
                      gettext('Mar'),
                      gettext('Apr'),
                      gettext('May'),
                      gettext('Jun'),
                      gettext('Jul'),
                      gettext('Aug'),
                      gettext('Sep'),
                      gettext('Oct'),
                      gettext('Nov'),
                      gettext('Dec')],
        loading: gettext('Loading...'),
        rangeSelectorFrom: gettext('From'),
        rangeSelectorTo: gettext('To'),
        rangeSelectorZoom: gettext('Zoom'),
        resetZoom: gettext('Reset zoom'),
        resetZoomTitle: gettext('Reset zoom level 1:1')
    }
});


$(document).ready(function() {
    // Kick off the application
    window.App = new KpiDashboard({
        el: document.getElementById('kpi-dash-app')
    });
});


}(jQuery));
