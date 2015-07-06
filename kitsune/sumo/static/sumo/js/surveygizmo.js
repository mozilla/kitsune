/* This sets up a couple of globals that SurveyGizmo can use to  hook
 * into the UI and provide surveys to users.
 *
 * This code was derived from the minified version of code posted in bug 1175880
 */
(function() {
    window.SurveyGizmoBeacon = 'sg_beacon';
    window.sg_beacon = window.sg_beacon || function() {
        window.sg_beacon.q = window.sg_beacon.q || [];
        window.sg_beacon.q.push(arguments);
    };
    var beaconScript = document.createElement('script');
    beaconScript.async = 1;
    beaconScript.src = '//d2bnxibecyz4h5.cloudfront.net/runtimejs/intercept/intercept.js';
    var lastScriptTag = document.getElementsByTagName('script')[0];
    lastScriptTag.parentNode.insertBefore(beaconScript, lastScriptTag);
})();
