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
        this.browser = this.searchString(this.dataBrowser);
        this.version = this.searchVersion(navigator.userAgent) ||
                       this.searchVersion(navigator.appVersion);
        this.OS = this.searchString(this.dataOS);
    },
    searchString: function (data, inputString) {
        for (var i = 0, l = data.length; i < l; i++) {
            // If an inputString is specified (for testing), use that.
            var matchedAll,
                dataString = inputString || data[i].string;

            this.versionSearchString = data[i].versionSearch || data[i].identity;

            // Check if all subStrings are in the dataString.
            matchedAll = _.reduce(data[i].subStrings, function(memo, sub) {
                return memo && (dataString.indexOf(sub) !== -1);
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
        return parseFloat(dataString.substring(index+this.versionSearchString.length+1));  // Turns "1.1.1" into 1.1 rather than 1.11. :-(
    },
    dataBrowser: [
        {
            string: navigator.userAgent,
            subStrings: ["Fennec"],
            versionSearch: "Fennec",
            identity: "m"
        },
        { // Fennec's UA changed in v14 to:
          // Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0
          // Now we need to look for the presence of both "Mobile"
          // and "Firefox".
            string: navigator.userAgent,
            subStrings: ["Mobile", "Firefox"],
            versionSearch: "Firefox",
            identity: "m"
        },
        {
            string: navigator.userAgent,
            subStrings: ["Firefox"],
            versionSearch: "Firefox",
            identity: "fx"
        }
    ],
    dataOS : [
        {
            string: navigator.platform,
            subStrings: ["Win"],
            identity: "win"
        },
        {
            string: navigator.platform,
            subStrings: ["Mac"],
            identity: "mac"
        },
        {
            string: navigator.userAgent,
            subStrings: ["Android"],
            identity: "android"
        },
        {
            string: navigator.userAgent,
            subStrings: ["Maemo"],
            identity: "maemo"
        },
        {
            string: navigator.platform,
            subStrings: ["Linux"],
            identity: "linux"
        }
    ]
};
BrowserDetect.init();  // TODO: Do this lazily.
