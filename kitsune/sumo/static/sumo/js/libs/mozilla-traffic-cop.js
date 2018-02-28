/* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// create namespace
if (typeof Mozilla === 'undefined') {
    var Mozilla = {};
}

/**
 * Traffic Cop traffic redirector for A/B/x testing
 *
 * Example usage:
 *
 * var cop = new Mozilla.TrafficCop({
 *     id: 'exp_firefox_new_all_link',
 *     cookieExpires: 48,
 *     variations: {
 *         'v=1': 25,
 *         'v=2': 25,
 *         'v=3': 25
 *     }
 * });
 *
 * cop.init();
 *
 *
 * @param Object config: Object literal containing the following:
 *      [String] id (required): Unique-ish string for cookie identification.
 *          Only needs to be unique to other currently running tests.
 *      [Number] cookieExpires (optional): Number of hours browser should
 *          remember the variation chosen for the user. Defaults to 24 (hours).
 *          A value of 0 will result in a session-length cookie.
 *      [Boolean] storeReferrerCookie (optional): Flag to specify whether or not
 *          original HTTP referrer should be placed in a cookie for later use.
 *          Defaults to true.
 *      [Function] customCallback (optional): Arbitrary function to run when
 *          a variation (or lack thereof) is chosen. This function will be
 *          passed the variation value (if chosen), or the value of
 *          noVariationCookieValue if no variation was chosen. *Specifying this
 *          function means no redirect will occur.*
 *      Object variations (required): Object holding key/value pairs of
 *          variations and their respective traffic percentages. Example:
 *
 *          variations: {
 *              'v=1': 20,
 *              'v=2': 20,
 *              'v=3': 20
 *          }
 */
Mozilla.TrafficCop = function(config) {
    'use strict';

    // make sure config is an object
    this.config = (typeof config === 'object') ? config : {};

    // store id
    this.id = this.config.id;

    // store variations
    this.variations = this.config.variations;

    // store total percentage of users targeted
    this.totalPercentage = 0;

    // store custom callback function (if supplied)
    this.customCallback = (typeof this.config.customCallback === 'function') ? this.config.customCallback : null;

    // store experiment cookie expiry (defaults to 24 hours)
    this.cookieExpires = (this.config.cookieExpires !== undefined) ? this.config.cookieExpires : Mozilla.TrafficCop.defaultCookieExpires;

    this.cookieExpiresDate = Mozilla.TrafficCop.generateCookieExpiresDate(this.cookieExpires);

    // store pref to store referrer cookie on redirect (default to true)
    this.storeReferrerCookie = (this.config.storeReferrerCookie === false) ? false : true;

    this.chosenVariation = null;

    // calculate and store total percentage of variations
    for (var v in this.variations) {
        if (this.variations.hasOwnProperty(v) && typeof this.variations[v] === 'number') {
            this.totalPercentage += this.variations[v];
        }
    }

    return this;
};

Mozilla.TrafficCop.defaultCookieExpires = 24;
Mozilla.TrafficCop.noVariationCookieValue = 'novariation';
Mozilla.TrafficCop.referrerCookieName = 'mozilla-traffic-cop-original-referrer';

/*
 * Initialize the traffic cop. Validates variations, ensures user is not
 * currently viewing a variation, and (possibly) redirects to a variation
 */
Mozilla.TrafficCop.prototype.init = function() {
    // respect the DNT
    if (typeof Mozilla.dntEnabled === 'function' && Mozilla.dntEnabled()) {
        return;
    }

    // If cookie helper is not defined or cookies are not enabled, do nothing.
    if (typeof Mozilla.Cookies === 'undefined' || !Mozilla.Cookies.enabled()) {
        return;
    }

    // make sure config is valid (id & variations present)
    if (this.verifyConfig()) {
        // determine which (if any) variation to choose for this user/experiment
        this.chosenVariation = Mozilla.TrafficCop.chooseVariation(this.id, this.variations, this.totalPercentage);

        // developer specified callback takes precedence
        if (this.customCallback) {
            this.initiateCustomCallbackRoutine();
        // if no customCallback is supplied, initiate redirect routine
        } else {
            this.initiateRedirectRoutine();
        }
    }
};

/*
 * Executes the logic around firing the custom callback specified by the
 * developer.
 */
Mozilla.TrafficCop.prototype.initiateCustomCallbackRoutine = function() {
    // set a cookie to remember the chosen variation
    Mozilla.Cookies.setItem(this.id, this.chosenVariation || Mozilla.TrafficCop.noVariationCookieValue, this.cookieExpiresDate);

    // invoke the developer supplied callback, passing in the chosen variation
    this.customCallback(this.chosenVariation);
};

/*
 * Executes logic around determining variation to which the visitor will be
 * redirected. May result in no redirect.
 */
Mozilla.TrafficCop.prototype.initiateRedirectRoutine = function() {
    var redirectUrl;

    // make sure current page doesn't match a variation
    // (avoid infinite redirects)
    if (!Mozilla.TrafficCop.isRedirectVariation(this.variations)) {
        // roll the dice to see if user should be send to a variation
        redirectUrl = Mozilla.TrafficCop.generateRedirectUrl(this.chosenVariation);

        // if we get a variation, send the user and store a cookie
        if (redirectUrl) {
            // Store the original referrer for use after redirect takes place so analytics can
            // keep track of where visitors are coming from.

            // Traffic Cop does nothing with this referrer - it's up to the implementing site to
            // send it on to an analytics platform (or whatever).
            if (this.storeReferrerCookie) {
                Mozilla.TrafficCop.setReferrerCookie(this.cookieExpiresDate);
            // a previous experiment may have set the cookie, so explicitly remove it here
            } else {
                Mozilla.TrafficCop.clearReferrerCookie();
            }

            // set a cookie containing the chosen variation
            Mozilla.Cookies.setItem(this.id, this.chosenVariation, this.cookieExpiresDate);

            Mozilla.TrafficCop.performRedirect(redirectUrl);
        } else {
            // if no variation, set a cookie so user isn't re-entered into
            // the dice roll on next page load
            Mozilla.Cookies.setItem(this.id, Mozilla.TrafficCop.noVariationCookieValue, this.cookieExpiresDate);

            // same as above - referrer cookie could be set from previous experiment, so best to clear
            Mozilla.TrafficCop.clearReferrerCookie();
        }
    }
};

/*
 * Ensures variations were provided and in total capture between 1 and 99%
 * of users.
 */
Mozilla.TrafficCop.prototype.verifyConfig = function() {
    if (!this.id || typeof this.id !== 'string') {
        return false;
    }

    // make sure totalPercent is between 0 and 100
    if (this.totalPercentage === 0 || this.totalPercentage > 100) {
        return false;
    }

    // make sure cookieExpires is null or a number
    if (typeof this.cookieExpires !== 'number') {
        return false;
    }

    return true;
};

/*
 * Generates an expiration date for the visitor's cookie.
 * 'date' param used only for unit testing.
 */
Mozilla.TrafficCop.generateCookieExpiresDate = function(cookieExpires, date) {
    // default to null, meaning a session-length cookie
    var d = null;

    if (cookieExpires > 0) {
        d = date || new Date();
        d.setHours(d.getHours() + cookieExpires);
    }

    return d;
};

/*
 * Checks to see if user is currently viewing a variation.
 */
Mozilla.TrafficCop.isRedirectVariation = function(variations, queryString) {
    var isVariation = false;
    queryString = queryString || window.location.search;

    // check queryString for presence of variation
    for (var v in variations) {
        if (queryString.indexOf('?' + v) > -1 || queryString.indexOf('&' + v) > -1) {
            isVariation = true;
            break;
        }
    }

    return isVariation;
};

/*
 * Returns the variation chosen for the current user/experiment.
 */
Mozilla.TrafficCop.chooseVariation = function(id, variations, totalPercentage) {
    var rando;
    var runningTotal;
    var choice = Mozilla.TrafficCop.noVariationCookieValue;

    // check to see if user has a cookie from a previously visited variation
    // also make sure variation in cookie is still valid (you never know)
    if (Mozilla.Cookies.hasItem(id) && (variations[Mozilla.Cookies.getItem(id)] || Mozilla.Cookies.getItem(id) === Mozilla.TrafficCop.noVariationCookieValue)) {
        choice = Mozilla.Cookies.getItem(id);
    // no cookie exists, or cookie has invalid variation, so choose a shiny new
    // variation
    } else {
        // conjure a random number between 1 and 100 (inclusive)
        rando = Math.floor(Math.random() * 100) + 1;

        // make sure random number falls in the distribution range
        if (rando <= totalPercentage) {
            runningTotal = 0;

            // loop through all variations
            for (var v in variations) {
                // check if random number falls within current variation range
                if (rando <= (variations[v] + runningTotal)) {
                    // if so, we have found our variation
                    choice = v;
                    break;
                }

                // tally variation percentages for the next loop iteration
                runningTotal += variations[v];
            }
        }
    }

    return choice;
};

/*
 * Generates a random percentage (between 1 and 100, inclusive) and determines
 * which (if any) variation should be matched.
 */
Mozilla.TrafficCop.generateRedirectUrl = function(chosenVariation, url) {
    var hash;
    var redirect;
    var urlParts;

    // url parameter only supplied for unit tests
    url = url || window.location.href;

    // strip hash from URL (if present)
    if (url.indexOf('#') > -1) {
        urlParts = url.split('#');
        url = urlParts[0];
        hash = urlParts[1];
    }

    // if a variation was chosen, construct a new URL
    if (chosenVariation !== Mozilla.TrafficCop.noVariationCookieValue) {
        redirect = url + (url.indexOf('?') > -1 ? '&' : '?') + chosenVariation;

        // re-insert hash (if originally present)
        if (hash) {
            redirect += '#' + hash;
        }
    }

    return redirect;
};

Mozilla.TrafficCop.performRedirect = function(redirectURL) {
    window.location.href = redirectURL;
};

Mozilla.TrafficCop.setReferrerCookie = function(expirationDate, referrer) {
    // in order of precedence, referrer should be:
    // 1. custom value passed in via unit test
    // 2. value of document.referrer
    // 3. 'direct' string literal
    referrer = referrer || Mozilla.TrafficCop.getDocumentReferrer() || 'direct';

    Mozilla.Cookies.setItem(Mozilla.TrafficCop.referrerCookieName, referrer, expirationDate);
};

Mozilla.TrafficCop.clearReferrerCookie = function() {
    Mozilla.Cookies.removeItem(Mozilla.TrafficCop.referrerCookieName);
};

// wrapper around document.referrer for better unit testing
Mozilla.TrafficCop.getDocumentReferrer = function() {
    return document.referrer;
};
