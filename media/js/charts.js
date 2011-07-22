/*
 * charts.js
 * Scripts to support charts.
 */

(function ($) {
    var data, dateToRevID;
    function init() {
        $('#show-chart').unbind('click');
        $('#show-chart').html(gettext('Loading...'));
        $('#show-chart').css('color', '#333333').css('cursor', 'auto').css('text-decoration', 'none');
        initChart();
    }

    function initChart() {
        $.ajax({
            type: "GET",
            url: $('#helpful-chart').data('url'),
            data: null,
            success: function (response) {
                data = response['data'];
                dateToRevID = response['date_to_rev_id'];
                if(data.length > 0) {
                    $('#helpful-chart').show('fast', function () {
                        stockChart();
                        $('#helpful-chart').append('<div id="chart-footnote">' + gettext('Query took: ') + response['query'] + gettext(' seconds') + '</div>')
                    });
                }
                else {
                    $('#show-chart').html(gettext('No votes data'));
                    $('#show-chart').unbind('click');
                }
            },
            error: function () {
                $('#show-chart').html(gettext('Error loading chart'));
                $('#show-chart').unbind('click');
            }
        });
    }

    /*
     * stockChart()
     * Creates the StockChart object with the defined options.
     * Requires data, plotLines, and dateToRevID to be set prior via AJAX.
     * The graph is drawn upon creation of the StockChart object.
     * Returns: nothing
     */
    function stockChart() {
        chart = new Highcharts.StockChart({
            chart: {
                renderTo: 'helpful-chart'
            },
            rangeSelector: {
                selected: 1
            },

            title: {
                text: gettext('Helpfulness Votes')
            },
            xAxis: {
                type: 'datetime',
                maxZoom: 14 * 24 * 3600000,  // fourteen days
                title: {
                    text: null
                }
            },
            yAxis: {
                title: {
                    text: gettext('Votes')
                }
            },
            tooltip: {
                style: {
                    width: 200
                }
            },
            credits: {
                enabled: false
            },
            plotOptions: {
                series: {
                    cursor: 'pointer',
                    point: {
                        events: {
                            mouseOver: function () {
                                $('#rev-list-' + dateToRevID[this.x]).addClass('graph-hover');
                            },
                            mouseOut: function () {
                                $('#rev-list-' + dateToRevID[this.x]).removeClass('graph-hover');
                            }
                        }
                    },
                    marker: {
                        lineWidth: 1
                    },
                    stickyTracking: true,
                }
            },
            series: data
        }, function () {
            $('#show-chart').hide();  // loading complete callback
        });
    }

    $('#show-chart').click(init);

}(jQuery));