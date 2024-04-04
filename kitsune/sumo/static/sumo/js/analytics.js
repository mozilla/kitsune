export default function trackEvent(name, parameters) {
  if (window.gtag) {
    console.log("------------------------------");
    console.log(`event: ${name}:`);
    console.log(`parameters: ${JSON.stringify(parameters, null, 2)}`);
    console.log("------------------------------");
    window.gtag('event', name, parameters);
  }
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
      if ((element.dataset.eventName === "link_click") && element.hasAttribute("href")) {
        if (!eventParameters) {
          eventParameters = {};
        }
        if ("link_url" in eventParameters === false) {
          eventParameters.link_url = element.getAttribute("href");
        }
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
