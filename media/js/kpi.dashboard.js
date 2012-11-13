/*
 * KPI Dashboard backbonejs app.
 */

(function($){

"use strict";

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


$(document).ready(function() {
    // Kick off the application
    window.App = new KpiDashboard({
        el: document.getElementById('kpi-dash-app')
    });
});


}(jQuery));
