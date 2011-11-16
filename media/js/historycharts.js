/*
 * Scripts to support charts on wiki article history.
 */

(function ($) {
    function init() {
        $('#show-chart').unbind('click');
        $('#show-chart').html(gettext('Loading...'));
        $('#show-chart').css('color', '#333333').css('cursor', 'auto').css('text-decoration', 'none');
        initChart();
    }

    function initChart() {
        var data, dateToRevID;
        $.ajax({
            type: "GET",
            url: $('#helpful-chart').data('url'),
            data: null,
            success: function (response) {
                data = response['data'];
                dateToRevID = response['date_to_rev_id'];
                dateTooltip = response['date_tooltip'];
                if(data.length > 0) {
                    $('#helpful-chart').show('fast', function () {
                        stockChart(data, dateToRevID, dateTooltip);
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
     * Requires data and dateToRevID to be passed in, populated via AJAX.
     * The graph is drawn upon creation of the StockChart object.
     * Returns: nothing
     */
    function stockChart(data, dateToRevID, dateTooltip) {
        Highcharts.setOptions({
            lang: {
                months: [gettext('January'), gettext('February'), gettext('March'), gettext('April'), gettext('May'), gettext('June'), gettext('July'), gettext('August'), gettext('September'), gettext('October'), gettext('November'), gettext('December')],
                weekdays: [gettext('Sunday'), gettext('Monday'), gettext('Tuesday'), gettext('Wednesday'), gettext('Thursday'), gettext('Friday'), gettext('Saturday')],
                loading: gettext('Loading...'),
                rangeSelectorFrom: gettext('From'),
                rangeSelectorTo: gettext('To'),
                rangeSelectorZoom: gettext('Zoom'),
                resetZoom: gettext('Reset zoom'),
                resetZoomTitle: gettext('Reset zoom level 1:1')
            }
        });

        chart = new Highcharts.StockChart({
            chart: {
                renderTo: 'helpful-chart',
                spacingBottom: 40,
            },
            legend: {
                enabled: true,
                y: 40,
            },
            rangeSelector: {
                selected: 5,
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
                },
                formatter: function(){
                    var x = this.x,
                        s;

                    if('key' in this) {
                        // revision/important date flag
                        s = ['<span style="font-size: 10px">' +
                            Highcharts.dateFormat('%b %e, %Y', x) +
                            '</span>',
                            '<strong>' + this.point.text + '</strong>']
                    }
                    else {
                        // data point element
                        s = ['<span style="font-size: 10px">' +
                            Highcharts.dateFormat('%A, %b %e, %Y', x) +
                            '</span>',
                            'Yes: <strong>' + dateTooltip[x].yes + '</strong>',
                            'No: <strong>' + dateTooltip[x].no + '</strong>',
                            'Percent: <strong>' + dateTooltip[x].percent + '%</strong>'
                            ]
                    }
                    return s.join('<br/>');
                },
                shared: true
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
        chart.series[0].hide();
        chart.series[1].hide();
    }
    $('#show-chart').click(init);
}(jQuery));
