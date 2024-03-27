export default function trackEvent(name, parameters) {
  console.log("--------------------");
  console.log(`event: "${name}"`);
  console.log(`parameters: ${JSON.stringify(parameters)}`);
  if (window.gtag) {
    console.log("sending...");
    window.gtag('event', name, parameters);
  }
  console.log("--------------------");
}

export function addGAEventListeners(containerSelector) {
  const elementsWithGAEvent = document.querySelectorAll(`${containerSelector} *[data-event-name]`);
  elementsWithGAEvent.forEach((elementWithGAEvent) => {
    elementWithGAEvent.addEventListener("click", (event) => {
      let eventParameters;
      const element = event.currentTarget;
      if (element.dataset.eventParameters) {
        eventParameters = JSON.parse(element.dataset.eventParameters);
      }
      trackEvent(element.dataset.eventName, eventParameters);
    });
  });
}

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  addGAEventListeners("body");
});
