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
  const linksWithGAEvent = document.querySelectorAll("body a[data-event-name]");
  const buttonsWithGAEvent = document.querySelectorAll("body button[data-event-name]");

  linksWithGAEvent.forEach((linkWithGAEvent) => {
    linkWithGAEvent.addEventListener("click", (event) => {
      let eventParameters;
      let link = event.currentTarget;
      // Is a new tab/window being opened?
      let newTab = event.metaKey || event.ctrlKey || link.getAttribute("target") === '_blank';

      if (link.dataset.eventParameters) {
        eventParameters = JSON.parse(link.dataset.eventParameters);
      }

      trackEvent(link.dataset.eventName, eventParameters);

      if (!newTab) {
        // Prevent the default action (navigation) while we wait for the event to be tracked.
        // If a new tab/window is being opened, there's no need to delay/prevent anything.
        event.preventDefault();
        // Delay the click navigation by 250ms to ensure the event is tracked.
        setTimeout(function () {
          document.location.href = link.getAttribute("href");
        }, 250);
      }
    });
  });

  buttonsWithGAEvent.forEach((buttonWithGAEvent) => {
    buttonWithGAEvent.addEventListener("click", (event) => {
      let eventParameters;
      let button = event.currentTarget;
      let closestForm = button.closest("form");

      if (button.dataset.eventParameters) {
        eventParameters = JSON.parse(button.dataset.eventParameters);
      }

      trackEvent(button.dataset.eventName, eventParameters);

      if (closestForm) {
        event.preventDefault();
        // Delay the form post by 250ms to ensure the event is tracked.
        setTimeout(function() {
          closestForm.dispatchEvent("submit");
        }, 250);
      }
    });
  });

});
