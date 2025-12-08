import BrowserDetect from "./browserdetect";
import RemoteTroubleshooting from "./remote";

/*
 * Prepopulate system info in AAQ form
 */

export default class AAQSystemInfo {
  static slugs = {
    desktop: ["/firefox/", "/firefox-enterprise/", "/thunderbird/"],
    mobile: ["/mobile/", "/ios/", "/focus-firefox/", "/thunderbird-android/"],
  };

  constructor(form) {
    this.form = form;

    // Autofill the user agent
    let userAgentInput = form.querySelector('input[name="useragent"]');
    if (userAgentInput) {
      userAgentInput.value = navigator.userAgent;
    }

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

    let ffVersionField = this.form.querySelector('input[name="ff_version"]');
    if (ffVersionField) {
      const browser = await detect.getBrowser();
      if (browser.mozilla) {
        ffVersionField.value =
          browser.version.toString();
      }
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
          let widget = this.form.querySelector("#id_troubleshooting");
          const widget_ariaDescribedby = widget.getAttribute("aria-describedby");
          if (widget_ariaDescribedby) {
            widget.setAttribute("aria-describedby", widget_ariaDescribedby + " troubleshooting-manual");
          } else {
            widget.setAttribute("aria-describedby", "troubleshooting-manual");
          }
        }
        this.form.querySelector("#troubleshooting-field").style.display =
          "block";
        return false;
      });
  }
}
