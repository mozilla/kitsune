// Detect the set of OSes and browsers we care about in the wiki and AAQ.
// Adapted from http://www.quirksmode.org/js/detect.html with these changes:
//
// * Changed the dataOS identity properties to lowercase to match the {for}
//   abbreviations in models.OPERATING_SYSTEMS.
// * Added Maemo and Android OS detection. Removed iPhone.
// * Added Fennec browser detection.
// * Changed Firefox's browser identity to "fx" and Fennec's to "m" to match
//   {for} syntax and avoid yet another representation.
// * Removed fallbacks to the string "an unknown ____" in favor of just
//   returning undefined.
// * Deleted the browsers we don't care about.
var BrowserDetect = {
    init: function () {
        var detected = this.detect();
        this.browser = detected[0];
        this.version = detected[1];
        this.OS = detected[2];
    },

    detect: function(inputString) {
        var browser = this.searchString(this.dataBrowser, inputString);
        var version;
        if (inputString) {
            version = this.searchVersion(inputString);
        } else {
            version = this.searchVersion(navigator.userAgent, inputString) ||
                           this.searchVersion(navigator.appVersion, inputString);
        }
        var os = this.searchString(this.dataOS, inputString);

        var res = this.fxosSpecialCase(inputString, browser, version, os);

        return res;
    },

    searchString: function (data, inputString) {
        for (var i = 0, l = data.length; i < l; i++) {
            // If an inputString is specified (for testing), use that.
            var matchedAll,
                dataString = inputString || data[i].string;

            this.versionSearchString = data[i].versionSearch || data[i].identity;

            // Check if all subStrings are in the dataString.
            matchedAll = _.reduce(data[i].subStrings, function(memo, sub) {
                if (sub instanceof RegExp) {
                    return memo && sub.exec(dataString);
                } else {
                    return memo && (dataString.indexOf(sub) !== -1);
                }
            }, true);

            if (matchedAll) {
                return data[i].identity;
            }
        }
    },

    searchVersion: function (dataString) {
        var index = dataString.indexOf(this.versionSearchString);
        if (index === -1) {
            return;
        }
        return parseFloat(dataString.substring(index+this.versionSearchString.length+1));  // Turns '1.1.1' into 1.1 rather than 1.11. :-(
    },

    fxosSpecialCase: function(ua, browser, version, os) {
        ua = ua || navigator.userAgent;
        var match = /Gecko\/([\d.]+)/.exec(ua);
        if (os === 'fxos' && !!match) {
            var geckoVersion = parseFloat(match[1]);
            version = this.dataGeckoToFxOS[geckoVersion];
            browser = 'fxos';
        }
        return [browser, version, os];
    },

    dataBrowser: [
        {
            string: navigator.userAgent,
            subStrings: ['Fennec'],
            versionSearch: 'Fennec',
            identity: 'm'
        },
        { // Fennec's UA changed in v14 to:
          // Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0
          // Now we need to look for the presence of both 'Mobile'
          // and 'Firefox'.
            string: navigator.userAgent,
            subStrings: ['Android', 'Firefox'],
            versionSearch: 'Firefox',
            identity: 'm'
        },
        {
            string: navigator.userAgent,
            subStrings: ['Firefox'],
            versionSearch: 'Firefox',
            identity: 'fx'
        }
    ],
    dataOS : [
        {
            // 6.2 is Windows 8. 6.3 is Windows 8.1.
            string: navigator.userAgent,
            subStrings: [/Windows NT 6.[23]/],
            identity: 'win8'
        },
        {   // 6.0 is Vista, 6.1 is Windows 7. We lump them together here.
            string: navigator.userAgent,
            subStrings: [/Windows NT 6\.[01]/],
            identity: 'win7'
        },
        {   // This lumps together Windows 2000 and Windows XP
            string: navigator.userAgent,
            subStrings: [/Windows NT 5\./],
            identity: 'winxp'
        },
        {   // If we can't figure out what version, fallback.
            // This probably means they are running something like Windows ME.
            string: navigator.platform,
            subStrings: ['Win'],
            identity: 'win'
        },
        {
            string: navigator.platform,
            subStrings: ['Mac'],
            identity: 'mac'
        },
        {
            string: navigator.userAgent,
            subStrings: ['Android'],
            identity: 'android'
        },
        {
            string: navigator.userAgent,
            subStrings: ['Maemo'],
            identity: 'maemo'
        },
        {
            string: navigator.platform,
            subStrings: ['Linux'],
            identity: 'linux'
        },
        {
            string: navigator.userAgent,
            subStrings: ['Firefox'],
            identity: 'fxos'
        }
    ],
    dataGeckoToFxOS: {
        18.0: 1.0,
        18.1: 1.1,
        26.0: 1.2,
        28.0: 1.3
    }
};
BrowserDetect.init();  // TODO: Do this lazily.
