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
window.ChartView = Backbone.View.extend({
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
                title: {
                    text: '%'
                }
            },
            xAxis: {
                type: 'datetime',
                tickInterval: 24 * 3600 * 1000 * 30,
                dateTimeLabelFormats: {
                    month: '%b'
                }
            },
            plotOptions: {
                line: {
                    dataLabels: {
                        enabled: true,
                        formatter: function() {
                            return this.y.toFixed(1) + '%';
                        }
                    },
                    enableMouseTracking: false
                }
            },
            title: {
                text: this.options.title
            },
            tooltip: {
                // TODO: Figure out why this is wonky.
                //enabled: true,
                formatter: function() {
                    return '<b>' + this.y.toFixed(1) + ' %</b>';
                }
            }
        };
    },

    render: function() {
        var self = this,
            data = this.model.get('objects');

        if(data) {
            self.chart = new Highcharts.Chart(self.chartOptions);
            _.each(this.options.series, function(series) {
                var mapper = series.mapper;
                if (!mapper) {
                    mapper = function(o){
                        return {
                            x: Date.parse(o['date']),
                            y: o[series.numerator] / o[series.denominator] * 100
                        };
                    };
                }
                self.chart.addSeries({
                    'data': _.map(data, mapper),
                    'name': series.name
                });
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

        // Create the views.
        this.solvedChartView = new ChartView({
            model: this.solvedChart,
            title: 'Questions Solved',
            series: [{
                name: 'Questions: % Solved',
                numerator: 'solved',
                denominator: 'questions'
            }]
        });

        this.voteChartView = new ChartView({
            model: this.voteChart,
            title: 'Article Helpful Votes',
            series: [{
                name: 'Article Votes: % Helpful',
                numerator: 'kb_helpful',
                denominator: 'kb_votes'
            }, {
                name: 'Answer Votes: % Helpful',
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

        this.fastResponseView = new ChartView({
            model: this.fastResponseChart,
            title: 'Questions responded to within 72 hours',
            series: [{
                name: 'Responded',
                numerator: 'responded',
                denominator: 'questions'
            }]
        });

        // Render the views.
        $(this.el)
            .append(this.solvedChartView.render().el)
            .append(this.voteChartView.render().el)
            .append(this.fastResponseView.render().el);

        // Load up the models.
        this.solvedChart.fetch();
        this.voteChart.fetch();
        this.fastResponseChart.fetch();
    }
});


$(document).ready(function() {
    // Kick off the application
    window.App = new KpiDashboard({
        el: document.getElementById('kpi-dash-app')
    });
});


}(jQuery));
