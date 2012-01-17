(function(){
    "use strict";
    var percent_chart = new Highcharts.Chart({
        chart: {
            renderTo: 'percent_answered',
            defaultSeriesType: 'column'
        },
        credits: {
            enabled: false
        },
        yAxis: {
            min: 0,

            title: {
                text: ''
            }
        },
       xAxis: {
            type: 'datetime',
        },
        title: {
            text: 'Percent Questions with solutions',
        },
        tooltip: {
            formatter: function() {
                return '<b>' + this.y.toFixed(1) + ' %';
            }
        },
    });
    $.ajax({
        url:  $('#kpi-dash').data('percent-answered-url'),
        context: document.body,
        success: function(data){
            percent_chart.addSeries({
                'data':  _.map(data.objects, function(o){
                    return {'x':Date.parse(o['date']),
                            'y':o['with_solutions'] / o['without_solutions'] * 100
                        }
                    }),
                'name': 'With Solutions',
            });
        }
    });


}(jQuery));
