(function ($) {
    function init() {
        initReadoutModes();
        initWatchMenu();
        initNeedsChange();
        initAnnouncements();
    }

    // Hook up readout mode links (like "This Week" and "All Time") to swap
    // table data.
    function initReadoutModes() {
        $(".readout-modes").each(
            function attachClickHandler() {
                var $modes = $(this),
                    slug = $modes.attr("data-slug");
                $modes.find(".mode").each(
                    function() {
                        var $button = $(this);
                        $button.click(
                            function switchMode() {
                                // Dim table to convey that its data isn't what
                                // the select mode indicates:
                                var $table = $("#" + slug + "-table");
                                $table.addClass("busy");

                                // Update button appearance:
                                $modes.find(".mode").removeClass("active");
                                $button.addClass("active");
                                $.get($button.attr("data-url"),
                                    function succeed(html) {
                                        $table.html(html).removeClass("busy");
                                    });
                                return false;
                            });
                    });
            });
    }

    function initWatchMenu() {
        var $watchDiv = $("#doc-watch"),
            $menu = $watchDiv.find(".popup-menu");

        // Initialize popup menu behavior:
        $watchDiv.find(".popup-trigger").click(
            function toggleMenu() {
                $menu.toggle();
            });

        // Teach checkboxes to dim and post on click:
        $watchDiv.find("input[type=checkbox]").click(
            // Dim the checkbox, post the watch change, then undim.
            function post() {
                var $box = $(this),
                    csrf = $box.closest("form")
                               .find("input[name=csrfmiddlewaretoken]").val(),
                    isChecked = $box.attr("checked");
                $box.attr("disabled", "disabled");
                $.ajax({
                        type: "POST",
                        url: isChecked ? $box.data("action-watch")
                                       : $box.data("action-unwatch"),
                        data: {csrfmiddlewaretoken: csrf},
                        success: function() {
                                $box.attr("disabled", "");
                            },
                        error: function() {
                                $box.attr("checked", isChecked ? ""
                                                               : "checked")
                                    .attr("disabled", "");
                            }
                    });
            });
    }

    function initNeedsChange() {
        // Expand rows on click
        $('#need-changes-table tr').click(function(e) {
            // Don't expand if a link was clicked.
            if(!$(e.target).is('a')) {
                $(this).toggleClass('active');
            }
        });
    }

    function initAnnouncements() {
        var $form = $('#create-announcement form');
        $form.find('button.btn-submit').on('click', function(ev) {
            ev.preventDefault();

            var $kbox = $('#create-announcement .kbox');

            $form.addClass('wait');
            $form.find('.error').remove();

            $.ajax({
                type: 'POST',
                url: $form.prop('action'),
                data: $form.serialize(),
                statusCode: {
                    200: function(data) {
                        $form.removeClass('wait');
                        $kbox.hide(200, function() {
                            $kbox.data('kbox').close();
                            $kbox.show();
                        });
                        var $success = $('#create-announcement').children('.success')
                            .show().css({ opacity: 1});

                        setTimeout(function() {
                            $success.animate({opacity: 0}, 1000);
                        }, 4000);
                    },
                    400: function(jxr) {
                        var data, field;
                        $form.removeClass('wait');
                        try {
                            data = JSON.parse(jxr.responseText);
                        } catch(e) {
                            data = {};
                        }
                        for (field in data) {
                            $form.find('[name=' + field + ']').parent()
                                .after('<li class="error">' + data[field] + '</li>');
                        }
                    }
                }
            });
        });

        $('.announcements li a.delete').on('click', function(ev) {
            ev.preventDefault();
            var $this = $(this);
            $.ajax({
                type: 'POST',
                url: $this.prop('href'),
                data: {
                    'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val()
                },
                success: function() {
                    $this.closest('li').remove();
                }
            });
        });
    }

    $(document).ready(init);
}(jQuery));
