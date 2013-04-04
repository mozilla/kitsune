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
                sets: true
            },
            sets: sets,
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

        graph.render();
    }

    $('#show-graph').click(init);
}(jQuery));
