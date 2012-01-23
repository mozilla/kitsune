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
                defaultSeriesType: 'column',
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
            title: {
                text: this.options.title,
            },
            tooltip: {
                formatter: function() {
                    return '<b>' + this.y.toFixed(1) + ' %</b>';
                }
            },
            legend: {
                enabled: false
            }
        };
    },

    render: function() {
        var self = this,
            data = this.model.get('objects');

        if(data) {
            self.chart = new Highcharts.Chart(self.chartOptions);
            _.each(this.options.series, function(series) {
                self.chart.addSeries({
                    'data': _.map(data, function(o){
                        return {
                            x: Date.parse(o['date']),
                            y: o[series.numerator] / o[series.denominator] * 100
                        };
                    })
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

        // Create the views.
        this.solvedChartView = new ChartView({
            model: this.solvedChart,
            title: 'Questions Solved',
            series: [{
                numerator: 'solved',
                denominator: 'questions'
            }]
        });

        this.voteChartView = new ChartView({
            model: this.voteChart,
            title: 'Article Helpful Votes',
            series: [{
                numerator: 'helpful',
                denominator: 'votes'
            }]
        });

        // Render the views.
        $(this.el)
            .append(this.solvedChartView.render().el)
            .append(this.voteChartView.render().el);

        // Load up the models.
        this.solvedChart.fetch();
        this.voteChart.fetch();
    }
});


// Kick off the application
window.App = new KpiDashboard({
    el: document.getElementById('kpi-dash-app')
});

}(jQuery));
