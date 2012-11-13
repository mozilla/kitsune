/*
 * kb dashboard chart
 */

(function($){

"use strict";

/*
 * Application
 */
window.KbDashboard = Backbone.View.extend({
    initialize: function() {
        // Create the models.
        this.voteChart = new ChartModel([], {
            url: $(this.el).data('vote-url')
        });

        // Create the views.
        this.voteChartView = new StockChartView({
            model: this.voteChart,
            title: gettext('Helpful Votes'),
            percent: true,
            width: 680,
            series: [{
                name: gettext('Article Votes: % Helpful'),
                numerator: 'kb_helpful',
                denominator: 'kb_votes',
                tooltip: {
                  ySuffix: '%',
                  yDecimals: 1
                }
            }]
        });

        // Render the views.
        $(this.el)
            .append(this.voteChartView.render().el);

        // Load up the models.
        this.voteChart.fetch();
    }
});


$(document).ready(function() {
    // Kick off the application
    window.App = new KbDashboard({
        el: document.getElementById('kb-helpfulness-chart')
    });
});


}(jQuery));
