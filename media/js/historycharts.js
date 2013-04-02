/*
 * Scripts to support Graphs on wiki article history.
 */

(function ($) {
    function init() {
        $('#show-graph').unbind('click');
        $('#show-graph').html(gettext('Loading...'));
        $('#show-graph').css('color', '#333333').css('cursor', 'auto').css('text-decoration', 'none');
        initGraph();
    }

    function initGraph() {
        var data, dateToRevID;
        $.ajax({
            type: "GET",
            url: $('#helpful-graph').data('url'),
            success: function (data) {
                if (data.series.length > 0) {
                    rickshawGraph(data);
                    $('#show-graph').hide();
                } else {
                    $('#show-graph').html(gettext('No votes data'));
                    $('#show-graph').unbind('click');
                }
            },
            error: function () {
                $('#show-graph').html(gettext('Error loading graph'));
                $('#show-graph').unbind('click');
            }
        });
    }

    function rickshawGraph(data) {
        var $container = $('#helpful-graph');
        var i, j;
        var lines, series, s;
        var annotations, $timelines;
        var annot, $timeline;
        var desiredMin;

        $container.show();
        var graph = new k.Graph($container, data.series, {
            options: {
                legend: false
            },
            hover: {
                xFormatter: function(seconds) {
                    var date = new Date(seconds * 1000);
                    return k.dateFormat('Week of %(year)s-%(month)s-%(date)s', date);
                },
                yFormatter: function(value) {
                    if (value > 0 && value <= 1.0) {
                        // This is probably a percentage.
                        return Math.floor(value * 100) + '%';
                    } else {
                        return Math.floor(value);
                    }
                }
            }
        });

        lines = {};
        series = graph.rickshaw.graph.series;
        for (i=0; i<series.length; i++) {
            s = series[i];
            lines[s.slug] = s;
        }

        lines.yes.color = '#21de2b';
        lines.no.color = '#de2b21';
        lines.percent.color = '#2b21de';

        $container.on('change', 'input[name=seriesset]', function(e) {
            switch($(this).val()) {
                case 'percent':
                    lines.percent.disabled = false;
                    lines.yes.disabled = true;
                    lines.no.disabled = true;
                    graph.rickshaw.graph.max = 1.0;
                    break;
                case 'votes':
                    lines.percent.disabled = true;
                    lines.yes.disabled = false;
                    lines.no.disabled = false;
                    graph.rickshaw.graph.max = undefined;
                    break;
            }
            graph.rickshaw.graph.update();
        });

        $container.find('input[name=seriesset][value=percent]')
            .prop('checked', true)
            .trigger('change');

        $timelines = $container.find('.timelines');
        for (i=0; i < data.annotations.length; i++) {
            annot = data.annotations[i];
            $timeline = $('<div class="timeline"/>').appendTo($timelines);
            annotations = new Rickshaw.Graph.Annotate({
                'graph': graph.rickshaw.graph,
                'element': $timeline[0]
            });

            for (j=0; j < annot.data.length; j++) {
                annotations.add(annot.data[j].x, annot.data[j].text);
            }
        }

        // About 6 months ago, as epoch seconds.
        desiredMin = (new Date() - (1000 * 60 * 60 * 24 * 180)) / 1000;
        graph.rickshaw.graph.window.xMin = desiredMin;
        graph.rickshaw.graph.update();

        graph.slider.slider('values', 0, desiredMin);
        function onSlide(event, ui) {
            var start = new Date(ui.values[0] * 1000);
            var end = new Date(ui.values[1] * 1000 - (1000 * 60 * 60 * 24));
            var fmt = '%(year)s-%(month)s-%(date)s';
            var label = interpolate('From %s to %s', [k.dateFormat(fmt, start),
                                                      k.dateFormat(fmt, end)]);
            $('label[for=slider]').text(label);
        }
        graph.slider.on('slide', onSlide);
        onSlide(null, {values: graph.slider.slider('values')} );

        graph.render();
    }

    $('#show-graph').click(init);
}(jQuery));
