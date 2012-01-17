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
            text: 'Questions and solutions',
        },
        tooltip: {
            formatter: function() {
                return '<b>' + this.percentage.toFixed(1) + ' %';
            }
        },
        plotOptions: {
            column: {
                stacking: 'percent'
            }
        },
    });
    $.ajax({
        url:  $('#kpi-dash').data('percent-answered-url'),
        context: document.body,
        success: function(data){
            console.log(_.map(data.objects, function(o){return {'x':Date.parse(o['date']),'y':o['without_solutions']}}));
            percent_chart.addSeries({
                'data':  _.map(data.objects, function(o){return {'x':Date.parse(o['date']),'y':o['without_solutions']}}),
                'name': 'Without Solutions',
            });
            percent_chart.addSeries({
                'data':  _.map(data.objects, function(o){return {'x':Date.parse(o['date']),'y':o['with_solutions']}}),
                'name': 'With Solutions',
            });
        }
    });


}(jQuery));
