/*
 * charts.js
 * Scripts to support charts.
 */

(function($){
    function init() {
        var data, plotLines, dateToRevID;
        $('#show-chart').unbind('click');
        $('#show-chart').html(gettext('Loading...'));
        initChart();
    }

    function initChart() {    
        $.ajax({type: "GET",
            url: $('#helpful-chart').data('url'), 
            data: null, 
            success: function(response) {
                $('#helpful-chart').show('fast', function() {
                    data = response['data'];
                    plotLines = response['plotLines'];
                    dateToRevID = response['date_to_rev_id'];
                    stockChart();
                    $('#helpful-chart').append('<div id="chart-footnote">' + gettext('Query took: ') + response['query'] + gettext(' seconds') + '</div>')
                });
            }, 
            error: function() {
                $('#show-chart').html(gettext('Error loading chart'));
                $('#show-chart').unbind('click');
            }
        });
    }
    
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
                maxZoom: 14 * 24 * 3600000, // fourteen days
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
                            mouseOver: function() {
                                $('#rev-list-' + dateToRevID[this.x]).addClass('graph-hover');
                            },
                            mouseOut: function() {
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
        }, function() { 
            $('#show-chart').hide();  // loading complete callback
        });
    }

    $('#show-chart').click(init);

}(jQuery));
