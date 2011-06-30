(function ($) {
    function init() {
        initReadoutModes();
        initWatchMenu();
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

    $(document).ready(init);
}(jQuery));
