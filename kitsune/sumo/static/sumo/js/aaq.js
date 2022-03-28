import BrowserDetect from "./browserdetect";
import RemoteTroubleshooting from "./remote";

/*
 * Prepopulate system info in AAQ form
 */

export default class AAQSystemInfo {
  static slugs = {
    desktop: ["desktop", "firefox-enterprise"],
    mobile: ["mobile", "ios", "focus"],
  };

  constructor(form) {
    this.form = form;

    // Autofill the user agent
    form.querySelector('input[name="useragent"]').value = navigator.userAgent;

    this.setupTroubleshootingInfo();
  }

  async fillDetails() {
    const detect = new BrowserDetect();
    const platform = await detect.getOS();

    const path = document.location.pathname;
    const platformMatchesSlug = Boolean(
      AAQSystemInfo.slugs[platform.mobile ? "mobile" : "desktop"].find((s) =>
        path.includes(s)
      )
    );
    if (!platformMatchesSlug) {
      return;
    }

    this.form.querySelector('input[name="os"]').value = platform.toString();

    const browser = await detect.getBrowser();
    if (browser.mozilla) {
      this.form.querySelector('input[name="ff_version"]').value =
        browser.version.toString();
    }
  }

  async setupTroubleshootingInfo(addEvent) {
    // If the troubleshoot input exists, try to get the data.
    if (!this.form.querySelector("#id_troubleshooting")) {
      // No troubleshooting form, so no point in trying to get the data.
      return;
    }

    const remote = new RemoteTroubleshooting();
    const dataPromise = remote.getData();

    this.form
      .querySelector("#share-data")
      .addEventListener("click", async (e) => {
        e.preventDefault();
        const data = await dataPromise;
        if (data?.application) {
          const json = JSON.stringify(data, null, 2);
          this.form.querySelector("#id_troubleshooting").value = json;
        } else {
          this.form.querySelector("#troubleshooting-button").style.display =
            "none";
          this.form.querySelector("#troubleshooting-manual").style.display =
            "block";
        }
        this.form.querySelector("#troubleshooting-field").style.display =
          "block";
        return false;
      });
  }
}
