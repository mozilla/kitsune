(function(){
    var percent_chart = new Highcharts.Chart({
        chart: {
            renderTo: 'percent_answered',
            type: 'pie'
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
        title: {
            text: 'Questions with solutions',
        },
        tooltip: {
            formatter: function() {
                return '<b>'+ this.point.name +'</b>: '+ this.percentage +' %';
            }
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    formatter: function() {
                        return '<b>'+ this.point.name +'</b>: '+ this.percentage +' %';
                    }
                }
            }
        },
        series: [{
            type: 'pie',
            name: 'Questions with solutions',
            data: [
            ]
        }]
    });
    $.ajax({
        url:  $('#kpi-dash').data('percent-answered-url'),
        context: document.body,
        success: function(data){
            console.log(data);
            percent_chart.addSeries({
                'data': [['With Solutions', data.data.solutions],
                        ['Without Solutions', data.data.without_solutions]]
            });
        }
    });


}(jQuery));
