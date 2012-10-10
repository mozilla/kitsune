/*
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
    initForTags: function(options, $container) {
        if (!$container) {
            $container = $('body');
        }
        options = $.extend({
            osSelector: '#os',
            browserSelector: '#browser'
        }, options);
        var self = this,
            $osMenu = $container.find(options.osSelector),
            $browserMenu = $container.find(options.browserSelector),
            $origBrowserOptions = $browserMenu.find('option').clone(),
            defaults = {
                mobile: {
                    browser: $origBrowserOptions.filter('[data-dependency="mobile"][data-default]').val(),
                    os: $osMenu.find('[data-dependency="mobile"][data-default]').val()
                },
                desktop: {
                    browser: $origBrowserOptions.filter('[data-dependency="desktop"][data-default]').val(),
                    os: $osMenu.find('[data-dependency="desktop"][data-default]').val()
                }
            },
            $body = $('body'),
            hash = self.hashFragment(),
            isSetManually,
            browserUsed,
            osUsed = BrowserDetect.OS;

        OSES = $osMenu.data('oses');  // {'mac': true, 'win': true, ...}
        BROWSERS = $browserMenu.data('browsers');  // {'fx4': {product: 'fx', maxFloatVersion: 4.9999}, ...}
        VERSIONS = $browserMenu.data('version-groups');  // {'fx': [[3.4999, '3'], [3.9999, '35']], 'm': [[1.0999, '1'], [1.9999, '11']]}
        MISSING_MSG = gettext('[missing header]');

        browserUsed = ShowFor.detectBrowser();

        function notListed(optionValue, $select) {
            // Return true if the $select doesn't have optionValue.
            return optionValue &&
                $select.find('option[value=' + optionValue + ']').length === 0;
        }

        if (notListed(browserUsed, $browserMenu)) {
            // If the browser used is not "officially" supported (shown in UI
            // by default) and is a browser we support in our backend, then
            // add it to the browser selections.
            ShowFor.addBrowserToSelect($browserMenu, browserUsed);
            $origBrowserOptions = $browserMenu.find('option').clone();
        }

        if (notListed(hash.browser, $browserMenu)) {
            // A browser can be forced to show up by using the hash params.
            ShowFor.addBrowserToSelect($browserMenu, hash.browser);
            $origBrowserOptions = $browserMenu.find('option').clone();
        }

        if (OSES[osUsed] && notListed(osUsed, $osMenu)) {
            // If the OS used is not "officially" supported (shown in UI
            // by default) and is an OS we support in our backend, then
            // add it to the OS selections.
            ShowFor.addOsToSelect($osMenu, osUsed);
        }

        if (OSES[hash.os] && notListed(hash.os, $osMenu)) {
            // An OS can be forced to show up by using the hash params.
            ShowFor.addOsToSelect($osMenu, hash.os);
        }


        // Make the 'Table of Contents' header localizable.
        $('#toc > h2').text(gettext('Table of Contents'));

        // Given a symbol like 'm4' or '=fx4', return something like
        // {comparator: '>', product: 'm', version: 4.9999}. Even if there's no
        // explicit comparator in the symbol, the comparator that's assumed
        // will be made explicit in the returned object. If it's not a known
        // product/version combo, return undefined.
        function conditionFromSymbol(symbol) {
            var slug, browser, comparator;

            // Figure out comparator:
            if (symbol.substring(0, 1) == '=') {
                comparator = '=';
                slug = symbol.substring(1);
            } else {  // If no leading =, assume >=.
                comparator = '>=';
                slug = symbol;
            }

            // Special case: fx3 and fx35 act like =fx3 and =fx35.
            if (slug == 'fx3' || slug == 'fx35') {
                comparator = '=';
            }

            browser = BROWSERS[slug];
            return {comparator: comparator,
                    product: browser.product,
                    version: browser.maxFloatVersion};
        }

        function updateForsAndToc(calledOnLoad) {
            // Hide and show document sections accordingly:
            showAndHideFors($osMenu.val(), $browserMenu.val());

            // Update the table of contents in case headers were hidden or shown:
            $('#toc > :not(h2)').remove(); // __TOC__ generates <ul/>'s.
            $('#toc').append(self.filteredToc($('#doc-content'), '#toc h2'));

            if (true === calledOnLoad) {
                // Called on document load. Scroll to hash if there is one.
                var hash = document.location.hash.substring(1),
                    element;
                if (hash) {
                    element = document.getElementById(hash);
                    if (element) {
                        element.scrollIntoView();
                    }
                }
            }
            return false;
        }

        // Set the {for} nodes to the proper visibility for the given OS and
        // browser combination.
        //
        // Hidden are {for}s that {list at least one OS but not the passed-in
        // one} or that {list at least one browser expression but none matching
        // the passed-in one}. Also, the entire condition can be inverted by
        // prefixing it with "not ", as in {for not mac,linux}.
        //
        // Takes a browser slug like "fx4" rather than a browser code and a
        // raw floating-point version because it has to be able to take both
        // detected browsers and slugs chosen explicitly from the <select>.
        function showAndHideFors(os, browser) {
            $container.find('.for').each(function(index) {
                var platform = $osMenu.find('option:selected').data('dependency'),
                    osAttrs = {},
                    foundAnyOses = false, foundAnyBrowsers = false,
                    forData,
                    isInverted,
                    shouldHide,
                    browserConditions = [];

                // Return whether the given browser slug matches any of the
                // given conditions. Passing a falsey slug results in false.
                // Passing an unknown slug results in undefined behavior. 
                // TODO: Implement with a generic any() instead--maybe underscore's.
                function meetsAnyOfConditions(slug, conditions) {
                    // Return whether a slug (like 'fx4' or 'fx35') meets a condition like
                    // {comparator: '>' product: 'm', version: 4.9999}.
                    function meets(slug, condition) {
                        var browser = BROWSERS[slug];
                        if (!slug || browser.product != condition.product) {
                            return false;
                        }
                        switch (condition.comparator) {
                            case '=':
                                // =fx35 --> {comparator: '=' browser: 'fx', version: 3.9999}
                                return browser.maxFloatVersion == condition.version;
                            case '>=':
                                // fx4 --> {comparator: '>=' browser: 'fx', version: 4.9999}
                                return browser.maxFloatVersion >= condition.version;
                            // Insert '<' here someday.
                        }
                        return false;
                    }

                    for (var i = 0; i < conditions.length; i++) {
                        if (meets(slug, conditions[i])) {
                            return true;
                        }
                    }
                }

                function slugWithoutComparators(slug) {
                    return (slug.substring(0, 1) == '=') ? slug.substring(1) : slug;
                }

                // If the data-for attribute is missing, return.
                forData = $(this).data('for');
                if (!forData) {
                    return;
                }

                // Catch the "not" operator if it's there:
                isInverted = forData.substring(0, 4) == 'not ';
                if (isInverted) {
                    forData = forData.substring(4);  // strip off "not "
                }

                // Divide {for} attrs into OSes and browsers:
                $(forData.split(',')).each(function(index) {
                    if (OSES[this] !== undefined) {
                        osAttrs[this] = true;
                        foundAnyOses = true;
                    } else if (BROWSERS[slugWithoutComparators(this)] !== undefined) {
                        browserConditions.push(conditionFromSymbol(this));
                        foundAnyBrowsers = true;
                    }
                });

                shouldHide = ((foundAnyOses && osAttrs[os] === undefined) ||
                              (foundAnyBrowsers && !meetsAnyOfConditions(browser, browserConditions))) &&
                             // Special cases:
                             // If the current selection is desktop:
                             // * Show the default mobile OS if no browser was specified or
                             //   the default mobile browser was also specified.
                             !(osAttrs[defaults.mobile.os] && platform === 'desktop' &&
                                (meetsAnyOfConditions(defaults.mobile.browser, browserConditions) || !foundAnyBrowsers)) &&
                             // * Show the default mobile browser if no OS was specified or
                             //   the default mobile OS was also specified.
                             !(meetsAnyOfConditions(defaults.mobile.browser, browserConditions) && platform === 'desktop' &&
                                (osAttrs[defaults.mobile.os] || !foundAnyOses)) &&
                             // If the current selection is mobile:
                             // * Show the default desktop OS if no browser was specified or
                             //   the default desktop browser was also specified.
                             !(osAttrs[defaults.desktop.os] && platform === 'mobile' &&
                                (meetsAnyOfConditions(defaults.desktop.browser, browserConditions) || !foundAnyBrowsers)) &&
                             // * Show the default desktop browser if no OS was specified or
                             //   the default desktop OS was also specified.
                             !(meetsAnyOfConditions(defaults.desktop.browser, browserConditions) && platform === 'mobile' &&
                                (osAttrs[defaults.desktop.os] || !foundAnyOses));

                if (shouldHide != isInverted) {
                    $(this).hide();  // saves original visibility, which is nice but not necessary
                } else {
                    $(this).show();  // restores original visibility
                }
            });
        }

        function updateShowforSelectors() {
            if ($.fn.selectbox) {
                $browserMenu.siblings('input.selectbox, div.selectbox-wrapper').remove();
                $osMenu.siblings('input.selectbox, div.selectbox-wrapper').remove();
                $browserMenu.selectbox();
                $osMenu.selectbox();
            } else {
                $browserMenu.removeAttr('disabled');
                $osMenu.removeAttr('disabled');
            }
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
            var options = {
                path: '/',
                expires: new Date()
            };
            // 12 hour expiration
            options.expires.setHours(options.expires.getHours() + 12);
            $.cookie("for_os", $osMenu.val(), options);
            $.cookie("for_browser", $browserMenu.val(), options);
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

            // Set the browser to the default version
            $browserMenu.val($browserMenu.find('option[data-default]').val());

            // Set browser to same version (frex, m4->fx4), if possible.
            var version = currentBrowser.replace(/^\D+/,'');
            $browserMenu.find('option').each(function() {
                var $this = $(this);
                if ($this.val().replace(/^\D+/,'') == version) {
                    $browserMenu.val($this.val());
                }
            });
            updateShowforSelectors();
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
                updateShowforSelectors();
            }
            return isManual;
        }

        // Set the selector value to the first option that doesn't
        // have the passed in dependency.
        function setSelectorDefault($select, dependency) {
            $select.val(
                $select.find('option:not([data-dependency="' + dependency +
                             '"])[data-default]').attr('value'));
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
                    if (BrowserDetect.OS && $detectedOS.length &&
                        $detectedOS.data('dependency') != currentDependency) {
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
        updateForsAndToc(true);

        updateShowforSelectors();
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
    addBrowserToSelect: function($select, browser) {
        // Adds the given browser to the passed <select/>.
        var $option = $('<option/>'),
            version,
            platform,
            highestVersion,
            lowestVersion,
            selector,
            sliceIndex;
        $option.attr('value', browser);
        if (browser.indexOf('fx') === 0) {
            platform = 'desktop';
            sliceIndex = 2;
        } else {
            platform = 'mobile';
            sliceIndex = 1;
        }
        version = parseInt(browser.slice(sliceIndex));
        $option.attr('data-dependency', platform);
        $option.text('Firefox ' + version);

        // Insert the option into the right spot to keep versions in order.
        // A little hacky, given fx35 is Firefox 3.5/3.6 and not Firefox 35.
        selector = 'option[data-dependency="' + platform + '"]';
        highestVersion = $select.find(selector + ':first').val();
        highestVersion = parseInt(highestVersion.slice(sliceIndex));
        lowestVersion = $select.find(selector + ':last').val();
        lowestVersion = parseInt(lowestVersion.slice(sliceIndex));
        if (lowestVersion === 35) {
            lowestVersion = 3.5;
        }
        if (version > highestVersion) {
            $select.prepend($option);
        } else if (version < lowestVersion) {
            $select.append($option);
        } else {
            // This will only be hit while we still officially support 3.6
            $option.insertBefore($select.find(selector + ':last'));
        }

        return $select;
    },
    addOsToSelect: function($select, os) {
        var $option = $('<option/>');
        $option.attr('value', os)
               .attr('text', os)
               .attr('data-dependency', 'mobile'); // This is only for Maemo at this point.
        $select.append($option);
    }
};

window.ShowFor = ShowFor;

})(jQuery);
