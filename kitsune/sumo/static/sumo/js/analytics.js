export default function trackEvent(name, parameters) {
  console.log("--------------------");
  console.log(`event: "${name}"`);
  console.log(`parameters: ${JSON.stringify(parameters)}`);
  console.log("--------------------");
  if (window.gtag) {
    window.gtag('event', name, parameters);
  }
}

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  const elementsWithGAEvent = document.querySelectorAll("body *[data-event-name]");
  elementsWithGAEvent.forEach((elementWithGAEvent) => {
    elementWithGAEvent.addEventListener("click", (event) => {
      let eventParameters;
      let element = event.currentTarget;
      if (element.dataset.eventParameters) {
        eventParameters = JSON.parse(element.dataset.eventParameters);
      }
      trackEvent(element.dataset.eventName, eventParameters);
    });
  });
});
