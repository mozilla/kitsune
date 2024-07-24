import UITour from "./libs/uitour";
import compareVersions from "./compare_versions";

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  let downloadButton = document.querySelector(".download-firefox .download-button");

  if (downloadButton) {
    let latestVersion = downloadButton.dataset.latestVersion;
    if (latestVersion) {
      UITour.getConfiguration("appinfo", function(info) {
        if (compareVersions(info.version, latestVersion) === 0) {
          document.querySelector(".refresh-firefox").hidden = false;
          document.querySelector(".download-firefox").hidden = true;
        }
      });
    }
  }
});
