const remoteTroubleshooting = {};
var data;

/**
 * Async method for retrieving remote-troubleshooting data.
 *
 * Tries to console.log problems to help diagnose issues.
 *
 * @param {function} callback - Callback function to call when
 * the data arrives. It should take a single argument which
 * will be the data packet.
 *
 * @param {integer} timeout - Timeout in milliseconds for calling
 * the callback with {} if the event hasn't yet gotten dispatched.
 * Defaults to 1000 ms (aka 1 second).
 *
 * @returns {object} with data in it or {}
 */
remoteTroubleshooting.getData = function(callback, timeout) {
  var timeoutId;

  // If we've already gotten the data, return that.
  if (data) {
    window.setTimeout(function() { callback(data); });
    return;
  }

  // If the browser is missing certain features, then asking for
  // remote-troubleshooting data is moot, so just drop out as
  // soon as we know important things are missing.
  if (!window.addEventListener) {
    // console.log('remoteTroubleshooting: browser does not support addEventListener');
    data = {};
    window.setTimeout(function() { callback(data); });
    return;
  }

  if (!(window.hasOwnProperty('CustomEvent') && typeof window.CustomEvent === 'function')) {
    // console.log('remoteTroubleshooting: browser does not support CustomEvent');
    data = {};
    window.setTimeout(function() { callback(data); });
    return;
  }

  timeout = timeout || 1000;

  /**
  * If the interval passes and the event listener hasn't kicked off then
  * there's nothing listening, so we abort.
  */
  function eject() {
    // console.log('remoteTroubleshooting: interval ' + timeout + ' has passed.');
    data = {};
    callback(data);
  }

  // Listen to the WebChannelMessageToContent event and handle
  // incoming remote-troubleshooting messages.
  window.addEventListener('WebChannelMessageToContent', function (e) {
    // FIXME: handle failure cases
    if (e.detail.id === 'remote-troubleshooting') {
      window.clearTimeout(timeoutId);

      data = e.detail.message;
      if (data === undefined) {
        // console.log('remoteTroubleshooting: data is {}. ' +
        //             'permission error? using http instead of https?');
        data = {};
      }

      window.setTimeout(function() { callback(data); });
    }
  });

  // Create the remote-troubleshooting event requesting data and
  // kick it off.
  var event = new window.CustomEvent('WebChannelMessageToChrome', {
    detail: {
      id: 'remote-troubleshooting',
      message: {
        command: 'request'
      }
    }
  });
  window.dispatchEvent(event);
  timeoutId = window.setTimeout(eject, timeout);
};

/**
* Returns whether or not the remote-troubleshooting data is
* available.
*
* @param {function} callback - Callback function to call when
* the data arrives. It should take a single argument which
* will be the data packet.
*
* @param {integer} timeout - Timeout in milliseconds for calling
* the callback with {} if the event hasn't yet gotten dispatched.
* Defaults to 1000 ms (aka 1 second).
*
* @returns {bool} true if it's available, false if it isn't
*/
remoteTroubleshooting.available = function(callback, timeout) {
  remoteTroubleshooting.getData(function (troubleShootingData) {
    // FIXME: This relies on the fact that 'application' is a
    // valid key with data in it. If it's not then, this will
    // be wrong.
    callback(!!troubleShootingData.application);
  }, timeout);
};

export default remoteTroubleshooting;
