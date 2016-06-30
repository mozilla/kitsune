/* globals _gaq:false */

function trackEvent(category, action, value) {
  if (_gaq) {
    _gaq.push(['_trackEvent', category, action, value]);
  }
}

let eventsToNotRepeat = new Set();

function trackEventOnce(category, action, value) {
  let key = `${category}::${action}::${value}`;
  if (eventsToNotRepeat.has(key)) {
    return false;
  } else {
    trackEvent(category, action, value);
    eventsToNotRepeat.add(key);
    return true;
  }
}

function scope(category) {
  return {
    trackEvent: trackEvent.bind(null, category),
    trackEventOnce: trackEventOnce.bind(null, category),
  };
}

export default {
  trackEvent,
  trackEventOnce,
  scope
};
