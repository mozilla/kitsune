/*
 * Scripts to support charts on contributor dashboard.
 */

(function($){
    function init() {
        $.ajax({type: "GET",
            url: $('#helpful-chart-tall').data('url'),
            data: null,
            success: function(response) {
                $('#helpful-chart-tall').show('fast', function() {
                    data = response['data'];
                    makeChart(data);
                });
            },
            error: function() {
                // Swallow AJAX errors
            }
        });
    }

    function makeChart(data) {
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'helpful-chart-tall',
                defaultSeriesType: 'scatter',
                zoomType: 'xy'
            },
            rangeSelector: {
                selected: 1
            },
            title: {
                text: gettext('Helpfulness Votes over 1 Month')
            },
            legend: {
                enabled: false,
            },
            xAxis: {
                title: {
                    text: gettext('Current Percent of Helpfulness')
                }
            },
            yAxis: {
                title: {
                    text: gettext('Percent Change in Helpfulness')
                }
            },
            tooltip: {
                formatter: function() {
                   return interpolate('<strong>%s</strong><br /><br />Helpfulness: %s% (%s%)<br />Total Votes: %s', [this.point.title, this.point.currperc, this.point.diffperc, this.point.total]);
                },
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
                            click: function() {
                                window.open(this.url);
                            }
                        }
                    },
                    stickyTracking: true,
                }
            },
            series: data
        });

        /* This is all drawing the legend via Highcharts SVG */
        $('<div id="chart-legend" style="text-align: center;"></div>').insertAfter('#helpful-chart-tall');
        var renderer = new Highcharts.Renderer($('#chart-legend')[0], 180, 60);
        var group = renderer.g().add();
        renderer.rect(1, 1, 175, 55, 5).attr({
            'stroke-width': 1,
            stroke: '#ABABAB',
            fill: 'white',
            zIndex: 0,
        }).add(group);

        renderer.text(gettext('Documents'), 57, 49).attr({
            zIndex: 20,
        }).css({
            color: '#4572A7',
            fontSize: '12px',
            'font-family': 'Helvetica, Arial, sans-serif',
        })
        .add(group);

        /* 10 */
        renderer.circle(20, 33, 3.207).attr({
            fill: '#bbbdbf',
            stroke: 'black',
            'stroke-width': 1,
            zIndex: 10,
        }).add(group);
        /* 100 */
        renderer.circle(20, 29, 6.856).attr({
            fill: '#99aebf',
            stroke: 'black',
            'stroke-width': 1,
            zIndex: 5,
        }).add(group);
        /* 500 */
        renderer.circle(20, 25, 11.661).attr({
            fill: '#0069bf',
            stroke: 'black',
            'stroke-width': 1,
            zIndex: 0,
        }).add(group);

        /* small */
        renderer.path(['M', 20, 30, 'H', 40]).attr({
            'stroke-width': 1,
            stroke: '#555555',
            zIndex: 20,
        }).add(group);
        /* med */
        renderer.path(['M', 20, 22, 'H', 80]).attr({
            'stroke-width': 1,
            stroke: '#555555',
            zIndex: 20,
        }).add(group);
        /* big */
        renderer.path(['M', 20, 13, 'H', 120]).attr({
            'stroke-width': 1,
            stroke: '#555555',
            zIndex: 20,
        }).add(group);

        /* small */
        renderer.text(interpolate('%s ' + gettext('Votes'), [10]), 40, 33).attr({
            zIndex: 20,
        }).css({
            color: '#4572A7',
            fontSize: '10px',
            'font-family': 'Helvetica, Arial, sans-serif',
        })
        .add(group);
        /* med */
        renderer.text(interpolate('%s ' + gettext('Votes'), [100]), 80, 26).attr({
            zIndex: 20,
        }).css({
            color: '#4572A7',
            fontSize: '10px',
            'font-family': 'Helvetica, Arial, sans-serif',
        })
        .add(group);
        /* big */
        renderer.text(interpolate('%s ' + gettext('Votes'), [500]), 120, 16).attr({
            zIndex: 20,
        }).css({
            color: '#4572A7',
            fontSize: '10px',
            'font-family': 'Helvetica, Arial, sans-serif',
        })
        .add(group);
    }

    $(document).ready(init);

}(jQuery));
