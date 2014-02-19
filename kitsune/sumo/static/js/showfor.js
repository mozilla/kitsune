/*global BrowserDetect:false, jQuery:false */
/*
 * ShowFor is a system to customize an article for an individual. It
 * will show or hide parts of an article based on spans with the class
 * "for" and a data attribute "data-for" which contains the show/hide
 * criteria.
 *
 * Depends on: browserdetect.js
 */

(function($) {

'use strict';

function ShowFor($container) {
    this.$container = $container || $('body');
    this.state = {};

    this.loadData();
    this.initEvents();
    this.updateUI();
    this.updateState();
    this.wrapTOCs();
    this.initShowFuncs();
    this.showAndHide();
}

ShowFor.prototype.productShortMap = {
    'fx': 'firefox',
    'm': 'mobile',
    'fxos': 'firefox-os',
    'tb': 'thunderbird'
};

/* Get the product/platform data from the DOM, and munge it into the
 * desired format. */
ShowFor.prototype.loadData = function() {
    this.data = JSON.parse(this.$container.find('.showfor-data').html());
    this.productSlugs = this.data.products.map(function(prod) {
        return prod.slug;
    });
    this.platformSlugs = this.data.platforms.map(function(platform) {
        return platform.slug;
    });
    this.versionSlugs = {};
    for (var prod in this.data.versions) {
        this.data.versions[prod].forEach(function(version) {
            this.versionSlugs[version.slug] = prod;
        }.bind(this));
    }
};

// Bind events for ShowFor.
ShowFor.prototype.initEvents = function() {
    window.onpopstate = this.updateUI.bind(this);
    this.$container.on('change keyup', 'input, select', this.onUIChange.bind(this));
};

/* Selects an option from a showfor selectbox, adding it if appropriate.
 *
 * If the desired value does not exist in the selectbox, this will consult the
 * possible versions (even those not shown to the user) to see if the option is
 * valid. If it is, it will be added, and then selected.
 *
 * This is useful because if the user comes to the site using something no
 * longer supported (Firefox 18 for example), then the UI will change to
 * include Firefox 18. Users that aren't running Firefox 18 won't see it as an
 * option though
 */
ShowFor.prototype.ensureSelect = function($select, type, product, val) {
    var $opt;
    var key;
    var extra = {};
    var target;

    function select(array, slug) {
        for (var i = 0; i < array.length; i++) {
            if (array[i].slug === slug) {
                return array[i];
            }
        }
        return null;
    }

    if (type === 'version') {
        target = select(this.data.versions[product], val);
        if (target !== null) {
            extra['data-min'] = target.min_version;
            extra['data-max'] = target.max_version;
        }
    } else if (type === 'platform') {
        target = select(this.data.platforms[product], val);
    } else if (type === 'product') {
        target = select(this.data.products, val);
    } else {
        throw new Error('Unknown showfor select type ' + type);
    }

    // This will fail if there is no version/product/platform that
    // matches the desired val.
    if (target === null) {
        return;
    }

    val = type + ':' + val;

    if ($select.find('option[value="' + val + '"]').length === 0) {
        $opt = $('<option>')
            .attr('value', val)
            .text(target.name);
        for (key in extra) {
            $opt.attr(key, extra[key]);
        }
        $select.append($opt);
    }

    $select.val(val);
};

/* Set up the UI. This consists of two parts:
 *   1. Pick initial values for the form elements. This is based on the first of
 *      the following criteria that matches:
 *      * url hash
 *      * sessionStore
 *      * browser detection via useragent sniffing.
 */
ShowFor.prototype.updateUI = function() {
    var persisted = null;
    var hash = document.location.hash;

    if (hash.indexOf(':') >= 0) {
        persisted = hash.slice(1);
    }

    if (persisted === null && window.sessionStorage) {
        // If the key doesn't exist, getItem will return null.
        persisted = sessionStorage.getItem('showfor::persist');
    }

    // Well, we got something. Lets try to parse it.
    if (persisted) {
        var itWorked = false;
        this.$container.find('.product input[type=checkbox]').prop('checked', false);
        persisted.split('&').forEach(function(prodInfo) {
            var data = prodInfo.split(':');
            var product = data[0] || null;
            var platform = data[1] || null;
            var version = data[2] || null;

            var $product = this.$container.find('.product[data-product="' + product + '"]');
            if ($product.length === 0) {
                return;
            }
            itWorked = true;
            $product.find('input[type=checkbox][value="product:' + product + '"]')
                    .prop('checked', true);
            if (platform) {
                var $platform = $product.find('select.platform');
                this.ensureSelect($platform, 'platform', product, platform);
            }
            if (version) {
                var $version = $product.find('select.version');
                this.ensureSelect($version, 'version', product, version);
            }
        }.bind(this));

        if (itWorked) {
            return;
        }
    }

    // This will only run if sessionstorage and url hash detection both failed.
    var browser = this.productShortMap[BrowserDetect.browser] || BrowserDetect.browser;
    var platform = this.productShortMap[BrowserDetect.OS] || BrowserDetect.OS;
    var version = BrowserDetect.version;

    var $products = this.$container.find('.product');
    var productElems = {};
    $products.each(function(i, elem) {
        var $elem = $(elem);
        productElems[$elem.data('product')] = $elem;
    });

    var verSlug, $version;

    if (browser === 'firefox' && this.productSlugs.indexOf('firefox') !== -1) {
        verSlug = 'fx' + version;
        $version = productElems.firefox.find('select.version');
        this.ensureSelect($version, 'version', verSlug);

    } else if (browser === 'mobile' && this.productSlugs.indexOf('mobile') !== -1) {
        verSlug = 'm' + version;
        $version = productElems.mobile.find('select.version');
        this.ensureSelect($version, 'version', verSlug);

    } else if (browser === 'firefox-os' && this.productSlugs.indexOf('firefox-os') !== -1) {
        verSlug = 'fxos' + version.toFixed(1);
        $version = productElems['firefox-os'].find('select.version');
        this.ensureSelect($version, 'version', verSlug);
    }

    $products.find('select.platform').each(function(i, elem) {
        this.ensureSelect($(elem), 'platform', platform);
    }.bind(this));
};

// Called when the user touches something.
ShowFor.prototype.onUIChange = function() {
    this.updateState();
    this.showAndHide();
    this.persist();
};

// Stores the current object state in the url hash and/or sessionStorage.
ShowFor.prototype.persist = function() {
    var key, val, i = 0;

    var persisted = '';
    for (key in this.state) {
        val = this.state[key];
        if (val.enabled) {
            if (i > 0) {
                persisted += '&';
            }
            var plat = val.platform || '';
            var ver = val.version ? (val.version.slug || '') : '';
            persisted += key + ':' + plat + ':' + ver;
            i++;
        }
    }

    // to avoid jumping to the top if all products are disabled.
    if (persisted === '') {
        return;
    }

    // If this is a navigation hash instead of a showfor hash, there
    // (probably) won't be any colons in it, so don't touch it.
    if (document.location.hash === '' || document.location.hash.indexOf(':') >= 0) {
        // Using document.location to change this triggers a popstate,
        // which we listen to. replaceState doesn't trigger a popstate.
        history.replaceState(this.state, persisted, '#' + persisted);
        // document.location.hash = persisted;
    }

    if (window.sessionStorage) {
        window.sessionStorage.setItem('showfor::persist', persisted);
    }
};

/* Parse the state of the form elements and store it.
 * 
 * This gets stored in this object's internal state, in the url via a
 * has, and into sessionstorage (if available) */
ShowFor.prototype.updateState = function() {
    this.state = {};

    this.$container.find('.product').each(function(i, elem) {
        var $elem = $(elem);
        var slug = $elem.data('product');
        this.state[slug] = {
            enabled: $elem.find('input[type=checkbox]').prop('checked')
        };

        $elem.find('select').each(function(i, elem) {
            var $elem = $(elem);
            var combined = $elem.val();
            var parts = combined.split(':');
            var type = parts[0];
            var data = parts[1];

            if (type === 'version') {
                var $option = $elem.find('option:selected');
                data = {
                    slug: data,
                    min: parseFloat($option.data('min')),
                    max: parseFloat($option.data('max'))
                };
            }

            this.state[slug][type] = data;
        }.bind(this));
    }.bind(this));
};

/* Table of Contents entries need to be shown shown and hidden too.
 * For any TOC entry that corresponds to a header that might be hidden,
 * wrap it in a span to mimic showfor elements. */
ShowFor.prototype.wrapTOCs = function() {
    /* This works by going through the TOC that already exists, and for
     * every element, checking if the corresponding heading in the
     * article is contained in a showfor. If it is, this wraps the TOC
     * element in <span>s that mimic showfor. */

     this.$container.find('#toc a').each(function(i, elem) {
        var $elem = $(elem);
        var idSelector = $elem.attr('href');
        if (idSelector[0] !== '#') {
            // No idea what to do here. Give up on this item.
            return;
        }

        var $docSearcher = $(idSelector);
        var $wrappee = $elem.parent();

        while ($docSearcher.length) {
            if ($docSearcher.hasClass('for')) {
                var $wrapper = $('<span/>', {
                    'class': 'for',
                    'data-for': $docSearcher.data('for')
                });
                $wrappee = $wrappee.wrap($wrapper);
            }
            $docSearcher = $docSearcher.parent();
        }
     });
};

/* Attach functions to each DOM element that determine whether it should
/* be shown or hidden. */
ShowFor.prototype.initShowFuncs = function() {
    this.$container.find('.for').each(function(i, elem) {
        var $elem = $(elem);
        var showFor = $elem.data('for');
        var criteria = showFor.split(/\s*,\s*/);
        var showFunc = this.matchesCriteria.bind(this, criteria);
        $elem.data('show-func', showFunc);
    }.bind(this));
};

/* Apply all the attached showfor functions for each DOM element.
 *
 * If no deciding function is attached, the element will be shown as a fallback.
 */
ShowFor.prototype.showAndHide = function() {
    this.$container.find('.for').each(function(i, elem) {
        var $elem = $(elem);
        var showFunc = $elem.data('show-func');
        if (showFunc) {
            $elem.toggle(showFunc());
        } else {
            $elem.show();
        }
    }.bind(this));
};

/* Checks if the current state of this object matches criteria.
 *
 * criteria is an array of strings like "fx24" or "not m", which
 * generally come from splitting the for selectors on commas.
 */
ShowFor.prototype.matchesCriteria = function(criteria) {
    /* The basic logic for showfor is that there are two kinds of
     * things: platforms and products. If one or more platforms are
     * in the criteria, at least one has to match. If one or more
     * products are in the criteria, at least one has to match.
     *
     * To be succinct, this has to be true for a set of criteria to match:
     *
     *    (any(browsers) or browsers.length == 0) and
     *    (any(platforms) or platforms.length == 0)
     *
     * Versions are seen as more specific products. Platforms don't
     * have versions.
     */
    var hasProduct = false;
    var matchProduct = false;
    var hasPlatform = false;
    var matchPlatform = false;

    /* This cheats a bit. Platforms are presented as being tied to a
     * platform, but we ignore that. Just assume that all selected
     * platforms apply to all products. */
    var enabledPlatforms = [];
    for (var slug in this.state) {
        var prod = this.state[slug];
        if (prod.enabled && prod.platform) {
            enabledPlatforms.push(prod.platform);
        }
    }

    /* This will loop through every item in criteria. It will set the
     * has/matches variables above to true if at least one
     * product/platform is found, and at least one of those matches
     * respectively. */
    criteria.forEach(function(name) {
        var productSlug, elemVersion;

        // Does this start with "not" ? Set a flag.
        var not = (name.indexOf('not') === 0);
        if (not) {
            name = name.replace(/^not ?/, '');
        }

        // "fx" -> "firefox", etc.
        name = this.productShortMap[name] || name;

        // Check for exact-equals. Maybe this will get smarter later.
        var oper = '>=';
        if (name[0] === '=') {
            name = name.slice(1);
            oper = '=';
        }

        /* Not that the below things never set anything false, only to
         * true. This way they work like a big OR. */

        // Is this a product? (without a version) {for fx}
        if (this.productSlugs.indexOf(name) >= 0) {
            hasProduct = true;
            if (this.state[name].enabled !== not) {
                matchProduct = true;
            }

        // Is this a product+version?  {for fx27}
        } else if (this.versionSlugs[name] !== undefined) {

            /* elemVersion is the version indicated in the element being
             * shown/hidden. stateMin and stateMax are the min and max
             * versions from this.state, which reflects the UI. */
            productSlug = this.versionSlugs[name];
            hasProduct = true;
            elemVersion = parseFloat(/^[a-z]+([\d\.]+)$/.exec(name)[1]);

            // name = 'fx27' -> productSlug = 'fx', elemVersion = 27

            var stateMin = this.state[productSlug].version.min;
            var stateMax = this.state[productSlug].version.max;

            var enabled = this.state[productSlug].enabled;
            var rightVersion = ((oper === '>=' && elemVersion < stateMax) ||
                                (oper === '=' && elemVersion >= stateMin && elemVersion < stateMax));

            if ((enabled && rightVersion) !== not) {
                matchProduct = true;
            }

        // Is it a platform?
        } else if (this.platformSlugs.indexOf(name) >= 0) {
            hasPlatform = true;

            if ((enabledPlatforms.indexOf(name) >= 0) !== not) {
                matchPlatform = true;
            }

        // Special case for windows.
        } else if (name === 'win') {
            /* Loop through each of the possible slugs for windows. If
             * any of them match, then this name matches. */
            var windowsTypes = ['winxp', 'win7', 'win8'];
            hasPlatform = true;
            var anyWin = false;
            windowsTypes.forEach(function(fakeName) {
                if ((enabledPlatforms.indexOf(fakeName) >= 0) !== not) {
                    anyWin = true;
                }
            });
            if ((anyWin && !not) || (!anyWin && not)) {
                matchPlatform = true;
            }
        }
    }.bind(this));

    // If a platform matches, or no platform matchers exist AND
    // if a product matches, or no product matchers exist.
    return (!hasProduct || matchProduct) && (!hasPlatform || matchPlatform);
};

window.ShowFor = ShowFor;

})(jQuery);
