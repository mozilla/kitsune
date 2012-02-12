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
window.MonthlyChartView = Backbone.View.extend({
    tagName: 'section',
    className: 'graph',

    initialize: function(s) {
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

    render: function() {
        var self = this,
            data = this.model.get('objects');

        if(data) {
            self.chart = new Highcharts.Chart(self.chartOptions);
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
                    name: series.name
                });
            });
        }

        return this;
    }
});

window.StockChartView = Backbone.View.extend({
    tagName: 'section',
    className: 'graph',

    initialize: function(s) {
        _.bindAll(this, 'render');

        this.model.bind('change', this.render);

        this.chartOptions = {
            chart: {
                renderTo: this.el,
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
                }
            },
            xAxis: {
                type: 'datetime',
                tickInterval: 24 * 3600 * 1000 * 30,
                dateTimeLabelFormats: {
                    month: '%b'
                }
            },
            yAxis: {
                min: 0,
                title: '%'
            },
            tooltip: {
                style: {
                    width: 200
                },
                yDecimals: 1,
                ySuffix: '%',
                shared: true,
                pointFormat: '<span style="color:{series.color}">{series.prettyName}</span>: <b>{point.y}</b><br/>'
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
    },

    render: function() {
        var self = this,
            data = this.model.get('objects');

        if(data) {
            _.each(this.options.series, function(series) {
                var seriesData;

                seriesData = _.map(data, function(o){
                    return [Date.parse(o['date']),
                            o[series.numerator] / o[series.denominator] * 100];
                });
                seriesData.reverse();

                // Add the series with 3 different possible groupings:
                // daily, weekly, monthly
                self.chartOptions.series.push({
                    name: gettext('Daily'),
                    data: seriesData,
                    dataGrouping: {
                        enabled: false
                    }
                });
                self.chartOptions.series.push({
                    name: gettext('Weekly'),
                    data: seriesData,
                    dataGrouping: {
                        forced: true,
                        units: [['week', [1]]]
                    }
                });
                self.chartOptions.series.push({
                    name: gettext('Monthly'),
                    data: seriesData,
                    dataGrouping: {
                        forced: true,
                        units: [['month', [1]]]
                    }
                });

                self.chart = new Highcharts.StockChart(self.chartOptions);

                self.chart.series[0].prettyName = self.chart.series[1].prettyName = self.chart.series[2].prettyName = series.name;

                // Hide the weekly and monthly series.
                self.chart.series[1].hide();
                self.chart.series[2].hide();
            });
        }
        return this;
    }
});


/*
 * Application
 */
window.KpiDashboard = Backbone.View.extend({
    initialize: function() {
        // Create the models.
        this.solvedChart = new ChartModel([], {
            url: $(this.el).data('solved-url')
        });

        this.voteChart = new ChartModel([], {
            url: $(this.el).data('vote-url')
        });

        this.fastResponseChart = new ChartModel([], {
            url: $(this.el).data('fastresponse-url')
        });

        this.activeKbContributorsChart = new ChartModel([], {
            url: $(this.el).data('active-kb-contributors-url')
        });

        this.activeAnswerersChart = new ChartModel([], {
            url: $(this.el).data('active-answerers-url')
        });

        // Create the views.
        this.solvedChartView = new StockChartView({
            model: this.solvedChart,
            title: gettext('Questions Solved'),
            percent: true,
            series: [{
                name: gettext('Solved'),
                numerator: 'solved',
                denominator: 'questions'
            }]
        });

        this.voteChartView = new MonthlyChartView({
            model: this.voteChart,
            title: gettext('Helpful Votes'),
            percent: true,
            series: [{
                name: gettext('Article Votes: % Helpful'),
                numerator: 'kb_helpful',
                denominator: 'kb_votes'
            }, {
                name: gettext('Answer Votes: % Helpful'),
                numerator: 'ans_helpful',
                denominator: 'ans_votes'
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

        this.fastResponseView = new StockChartView({
            model: this.fastResponseChart,
            title: gettext('Questions responded to within 72 hours'),
            percent: true,
            series: [{
                name: gettext('Responsed'),
                numerator: 'responded',
                denominator: 'questions'
            }]
        });

        this.activeKbContributorsView = new MonthlyChartView({
            model: this.activeKbContributorsChart,
            title: gettext('Active KB Contributors'),
            series: [{
                name: 'en-US',
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['en_us']
                    };
                }
            }, {
                name: 'non en-US',
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['non_en_us']
                    };
                }
            }]
        });

        this.activeAnswerers = new MonthlyChartView({
            model: this.activeAnswerersChart,
            title: gettext('Active Support Forum Contributors'),
            series: [{
                name: gettext('Contributors'),
                mapper: function(o) {
                    return {
                        x: Date.parse(o['date']),
                        y: o['contributors']
                    };
                }
            }]
        });

        // Render the views.
        $(this.el)
            .append(this.solvedChartView.render().el)
            .append(this.fastResponseView.render().el)
            .append(this.voteChartView.render().el)
            .append(this.activeKbContributorsView.render().el)
            .append(this.activeAnswerers.render().el);


        // Load up the models.
        this.solvedChart.fetch();
        this.fastResponseChart.fetch();
        this.activeKbContributorsChart.fetch();
        this.activeAnswerersChart.fetch();
        this.voteChart.fetch();
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
