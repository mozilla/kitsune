/*
 * showfor.js
 * Scripts for the showfor browser/os detection.
 *
 * Depends on: browserdetect.js
 * Optional for dhtml selects: jquery.selectbox-1.2.js
 */

(function($) {

"use strict";  // following the Ricky kbox awesomeness


var OSES, BROWSERS, VERSIONS, MISSING_MSG;
var ShowFor = {
    // Return the browser and version that appears to be running. Possible
    // values resemble {fx4, fx35, m1, m11}. Return undefined if the currently
    // running browser can't be identified.
    detectBrowser: function() {
        function getVersionGroup(browser, version) {
            if ((browser === undefined) || (version === undefined) || !VERSIONS[browser]) {
                return;
            }

            for (var i = 0; i < VERSIONS[browser].length; i++) {
                if (version < VERSIONS[browser][i][0]) {
                    return browser + VERSIONS[browser][i][1];
                }
            }
        }
        return getVersionGroup(BrowserDetect.browser, BrowserDetect.version);
    },

    // Treat the hash fragment of the URL as a querystring (e.g.
    // #os=this&browser=that), and return an object with a property for each
    // param. May not handle URL escaping yet.
    hashFragment: function() {
        var o = {},
            args = document.location.hash.substr(1).split('&'),
            chunks;
        for (var i = 0; i < args.length; i++) {
            chunks = args[i].split('=');
            o[chunks[0]] = chunks[1];
        }
        return o;
    },

    // Hide/show the proper page sections that are marked with {for} tags as
    // applying to only certain browsers or OSes. Update the table of contents
    // to reflect what was hidden/shown.
    initForTags: function() {
        var self = this,
            $osMenu = $('#os'),
            $browserMenu = $('#browser'),
            $origBrowserOptions = $browserMenu.find('option').clone(),
            $body = $('body'),
            hash = self.hashFragment(),
            isSetManually;

        OSES = $osMenu.data('oses');  // {'mac': true, 'win': true, ...}
        BROWSERS = $browserMenu.data('browsers');  // {'fx4': true, ...}
        VERSIONS = $browserMenu.data('version-groups');  // {'fx': [[3.4999, '3'], [3.9999, '35']], 'm': [[1.0999, '1'], [1.9999, '11']]}
        MISSING_MSG = gettext('[missing header]');

        // Make the 'Table of Contents' header localizable.
        $('#toc > h2').text(gettext('Table of Contents'));

        function updateForsAndToc() {
            // Hide and show document sections accordingly:
            self.showAndHideFors($('select#os').val(),
                                 $('select#browser').val());

            // Update the table of contents in case headers were hidden or shown:
            $('#toc > :not(h2)').remove(); // __TOC__ generates <ul/>'s.
            $('#toc').append(self.filteredToc($('#doc-content'), '#toc h2'));

            return false;
        }

        // If there isn't already a hash for purposes of actual navigation,
        // stick our {for} settings in there.
        function updateHashFragment() {
            var hash = self.hashFragment();

            // Kind of a shortcut. What we really want to know is "Is there anything in the hash fragment that isn't a {for} selector?"
            if (!document.location.hash || hash.hasOwnProperty("os") || hash.hasOwnProperty("browser")) {
                var newHash = "os=" + $osMenu.val() + "&browser=" + $browserMenu.val();
                document.location.replace(document.location.href.split('#')[0] + '#' + newHash);
            }
        }

        // Persist the menu selection in a cookie and hash fragment.
        function persistSelection() {
            $.cookie("for_os", $osMenu.val(), {path: '/'});
            $.cookie("for_browser", $browserMenu.val(), {path: '/'});
            updateHashFragment();
        }

        // Clear the menu selection cookies.
        function clearSelectionCookies() {
            $.cookie("for_os", null, {path: '/'});
            $.cookie("for_browser", null, {path: '/'});
        }

        // Get the dependency based on the currently selected OS
        function getCurrentDependency() {
            return $osMenu.find('[value="' + $osMenu.val() + '"]')
                          .data('dependency');
        }

        //Handle OS->Browser dependencies
        function handleDependencies(evt, noRedirect) {
            var currentDependency = getCurrentDependency(),
                currentBrowser, newBrowser, availableBrowsers;

            if (!noRedirect && $body.is('.mobile, .desktop') &&
                !$body.is('.' + currentDependency)) {
                // If we are on the mobile page and select a desktop OS,
                // redirect to the desktop home page. And vice-versa.
                // TODO: maybe use data-* attrs for the URLs?
                persistSelection();
                var url = document.location.href;
                if ($body.is('.mobile')) {
                    document.location = url.replace('/mobile', '/home');
                } else {
                    document.location = url.replace('/home', '/mobile');
                }
            }

            currentBrowser = $browserMenu.val();
            availableBrowsers = $origBrowserOptions.filter(
                '[data-dependency="' + currentDependency + '"]');
            $browserMenu.empty().append(availableBrowsers);

            // Set browser to same version (frex, m4->fx4), if possible.
            var version = currentBrowser.replace(/^\D+/,'');
            $browserMenu.find('option').each(function() {
                var $this = $(this);
                if ($this.val().replace(/^\D+/,'') == version) {
                    $browserMenu.val($this.val());
                }
            });
            self.updateShowforSelectors();
        }

        // Select the right item from the browser or OS menu, taking cues from
        // the following places, in order: the URL hash fragment, the cookie,
        // and client detection. Return whether the item appears to have
        // selected manually: that is, via a cookie or a hash fragment.
        function setSelectorValue(cookieName, hashName, hash, detector, $menu) {
            var initial = hash[hashName],
                isManual = true;
            if (!initial) {
                initial = $.cookie(cookieName);
                if (!initial) {
                    initial = detector();
                    isManual = false;
                }
            }
            if (initial) {
                $menu.val(initial);  // does not fire change event
                self.updateShowforSelectors();
            }
            return isManual;
        }

        // Set the selector value to the first option that doesn't
        // have the passed in dependency.
        function setSelectorDefault($select, dependency) {
            $select.val(
                $select.find('option:not([data-dependency="' + dependency +
                             '"]):first').attr('value'));
        }

        // If we are on mobile or desktop home page, make sure
        // appropriate OS is selected
        function checkSelectorValues() {
            var currentDependency,
                isManual = false;

            if ($body.is('.desktop, .mobile')) {
                currentDependency = getCurrentDependency();
                // currentDependency will be 'desktop' or 'mobile'
                // Make sure we are on the corresponding home page. Otherwise,
                // change the selection appropriately.
                if (!$body.is('.' + currentDependency)) {
                    var $detectedOS = $osMenu.find('[value=' + BrowserDetect.OS + ']');
                    if ($detectedOS.data('dependency') != currentDependency) {
                        // The detected OS is valid. Make it the new selection.
                        $osMenu.val($detectedOS.attr('value'));
                        $browserMenu.val(ShowFor.detectBrowser());
                        clearSelectionCookies();
                    } else {
                        // Force a new selection.
                        setSelectorDefault($osMenu, currentDependency);
                        setSelectorDefault($browserMenu, currentDependency);

                        // Set the cookie so that the selection sticks when
                        // browsing to articles.
                        persistSelection();
                        isManual = true;
                    }
                }
            }
            return isManual;
        }

        // Select the sniffed, cookied, or hashed browser or OS if there is one:
        isSetManually = setSelectorValue("for_os", "os", hash, function() { return BrowserDetect.OS; }, $osMenu);
        isSetManually |= setSelectorValue("for_browser", "browser", hash, ShowFor.detectBrowser, $browserMenu);
        isSetManually |= checkSelectorValues();

        // Possibly change the settings based on dependency rules:
        handleDependencies(null, true);

        if (isSetManually) {
            updateHashFragment();
        }

        $osMenu.change(handleDependencies);
        $osMenu.change(persistSelection);
        $osMenu.change(updateForsAndToc);
        $browserMenu.change(persistSelection);
        $browserMenu.change(updateForsAndToc);

        // Fire off the change handler for the first time:
        updateForsAndToc();
    },

    // Return a table of contents (an <ul>) listing the visible headers within
    // elements in the $pageBody set.
    //
    // The highest header level found within $pageBody is considered to be the
    // top of the TOC: if $pageBody has h2s but no h1s, h2s will be used as the
    // first level of the TOC. Missing headers (such as if you follow an h2
    // directly with an h4) are noted prominently so you can fix them.
    //
    // excludesSelector is an optional jQuery selector for excluding certain
    // headings from the table of contents.
    filteredToc: function($pageBody, excludesSelector) {
        function headerLevel(index, hTag) {
            return parseInt(hTag.tagName.charAt(1), 10);
        }

        var $headers = $pageBody.find(':header:not(:hidden)'),  // :hidden is a little overkill, but it's short.
            $root = $('<ul />'),
            $cur_ul = $root,
            ul_level = Math.min.apply(Math, $headers.map(headerLevel).get());

        // For each header in the document, look upward until you hit something that's hidden. If nothing is found, add the header to the TOC.
        $headers.each(function addIfShown(index) {
            var h_level = headerLevel(0, this),
                $h = $(this);

            if (excludesSelector && $h.is(excludesSelector)) {
                // Skip excluded headers.
                return;
            }

            // If we're too far down the tree, walk up it.
            for (; ul_level > h_level; ul_level--) {
                $cur_ul = $cur_ul.parent().closest('ul');
            }

            // If we're too far up the tree, walk down it, create <ul>s until we aren't:
            for (; ul_level < h_level; ul_level++) {
                var $last_li = $cur_ul.children().last();
                if ($last_li.length === 0) {
                    $last_li = $('<li />').append($('<em />')
                                                  .text(MISSING_MSG))
                                          .appendTo($cur_ul);
                }
                // Now the current <ul> ends in an <li>, one way or another.
                $cur_ul = $('<ul />').appendTo($last_li);
            }

            // Now $cur_ul is at exactly the right level to add a header by appending an <li>.
            // Clone the header, remove any hidden elements and get the text,
            // and replace back with the clone.
            var $tmpClone = $h.clone(),
                text = $h.find(':hidden').remove().end().text();
            $h.replaceWith($tmpClone);
            $cur_ul.append($('<li />').text(text).wrapInner($('<a>').attr('href', '#' + $h.attr('id'))));
        });
        return $root;
    },

    // Set the {for} nodes to the proper visibility for the given OS and
    // browser combination.
    //
    // Hidden are {for}s that {list at least one OS but not the passed-in one}
    // or that {list at least one browser but not the passed-in one}. Also, the
    // entire condition can be inverted by prefixing it with "not ", as in {for
    // not mac,linux}.
    showAndHideFors: function(os, browser) {
        $('.for').each(function(index) {
            var osAttrs = {}, browserAttrs = {},
                foundAnyOses = false, foundAnyBrowsers = false,
                forData,
                isInverted,
                shouldHide;

            // Catch the "not" operator if it's there:
            forData = $(this).data('for');
            if (!forData) {
                // If the data-for attribute is missing, move on.
                return;
            }

            isInverted = forData.substring(0, 4) == 'not ';
            if (isInverted) {
                forData = forData.substring(4);  // strip off "not "
            }

            // Divide {for} attrs into OSes and browsers:
            $(forData.split(',')).each(function(index) {
                if (OSES[this] != undefined) {
                    osAttrs[this] = true;
                    foundAnyOses = true;
                } else if (BROWSERS[this] != undefined) {
                    browserAttrs[this] = true;
                    foundAnyBrowsers = true;
                }
            });

            shouldHide = ((foundAnyOses && osAttrs[os] == undefined) ||
                         (foundAnyBrowsers && browserAttrs[browser] == undefined)) &&
                         // Special cases ):
                         // TODO: make this easier to maintain somehow?
                         // Show android/m4 on desktop selection
                         !(osAttrs['android'] && os !== 'maemo' /* only one mobile browser ATM */) &&
                         !(browserAttrs['m4'] && browser !== 'm4' && (osAttrs['android'] || !foundAnyOses)) &&
                         // Show win/fx4 on mobile selection
                         !(osAttrs['win'] && (os === 'android' || os == 'maemo') && (browserAttrs['fx4'] || !foundAnyBrowsers)) &&
                         !(browserAttrs['fx4'] && browser === 'm4' && (osAttrs['win'] || !foundAnyOses));

            if ((shouldHide && !isInverted) || (!shouldHide && isInverted)) {
                $(this).hide();  // saves original visibility, which is nice but not necessary
            }
            else {
                $(this).show();  // restores original visibility
            }
        });
    },

    updateShowforSelectors: function() {
        if ($.fn.selectbox) {
            $('#support-for input.selectbox, #support-for div.selectbox-wrapper').remove();
            $('#support-for select').selectbox();
        } else {
            $('#support-for select').removeAttr('disabled');
        }
    }

};

window.ShowFor = ShowFor;

})(jQuery);
