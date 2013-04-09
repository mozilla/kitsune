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
        var sets = {};

        sets[gettext('Votes')] = ['yes', 'no'];
        sets[gettext('Percent')] = ['percent'];

        $container.show();
        var graph = new k.Graph($container, {
            data: data,
            options: {
                legend: false,
                sets: true,
                bucket: true
            },
            metadata: {
                sets: sets,
                bucketMethods: {
                    'percent': 'average'
                }
            }
        });

        graph.render();
    }

    $('#show-graph').click(init);
}(jQuery));
