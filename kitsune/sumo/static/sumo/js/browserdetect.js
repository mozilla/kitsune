import RemoteTroubleshooting from "sumo/js/remote";

export class Version {
  major;
  minor;
  patch;
  label;

  static order = ["major", "minor", "patch", "label"];

  constructor(string = "") {
    [, string, this.label] = string.match(/([\d\.]*)([ab]\d*)?/i);
    [this.major, this.minor, this.patch] = string
      .split(".")
      .map((x) => parseInt(x, 10));
  }

  toString(cutoff) {
    let string = "";
    for (const position of Version.order) {
      const number = this[position];
      if (position === "label") {
        if (number) {
          string += number;
        }
      } else if (cutoff && isNaN(number)) {
        string += ".0";
      } else if (isNaN(number)) {
        break;
      } else {
        string += "." + number.toString();
      }
      if (cutoff === position) {
        break;
      }
    }
    return string.slice(1);
  }
}

class Browser {
  mozilla = false;
  brands;
  version;
}

class OS {
  name;
  version;

  get mobile() {
    return ["Android", "iOS"].includes(this.name);
  }

  toString() {
    let string = this.name;
    if (this.version) {
      string += " " + this.version;
    }
    return string;
  }

  static versionNormalization = {
    Windows: {
      "nt 5.1": "XP",
      "nt 5.2": "XP",
      "nt 6.0": "Vista",
      "nt 6.1": "7",
      "nt 6.2": "8",
      "nt 6.3": "8.1",
      "nt 6.4": "10",
      "nt 10.0": "10",
    },
  };
}

class GenericDetector {
  async browser(browser = new Browser()) {
    return browser;
  }

  async os(os = new OS()) {
    return os;
  }
}

export class UADetector extends GenericDetector {
  uaString;

  constructor(uaString = navigator.userAgent) {
    super();
    this.uaString = uaString;
  }

  async browser(browser = new Browser()) {
    let isMozilla = this.uaString.match(UADetector.mozillaRegex);
    if (isMozilla) {
      browser.mozilla = true;
      let { name, version } = isMozilla.groups;
      name = name.toLowerCase();

      let brands = UADetector.brandNormalization[name] ?? [];
      let os = await this.os();
      if (!os.mobile) {
        // remove Focus from possible brands if we're not on mobile
        brands = brands.filter((x) => x !== "Firefox Focus");
      }

      browser.brands = brands;
      browser.version = new Version(version);
    }
    return browser;
  }

  static mozillaRegex =
    /(?<name>Firefox|FxiOS|Fennec|Focus|Klar|Thunderbird)\/(?<version>[0-9\._]+)?/i;

  static brandNormalization = {
    firefox: ["Firefox", "Firefox Focus"],
    fxios: ["Firefox", "Firefox Focus"],
    fennec: ["Firefox"],
    focus: ["Firefox Focus"],
    klar: ["Firefox Focus"],
    thunderbird: ["Thunderbird"],
  };

  async os(os = new OS()) {
    for (const [name, regex] of UADetector.osRegexps) {
      const matches = this.uaString.match(regex);
      if (matches) {
        let version = matches?.groups?.version.toLowerCase();
        version = OS.versionNormalization?.[name]?.[version] ?? version;
        os.name = name;
        os.version = version;
        return os;
      }
    }
  }

  static osRegexps = [
    ["Windows", /Windows ?(?<version>(?:NT )?[0-9a-z\._]+)?/i],
    ["iOS", /(iPhone)|(iPad)|(iPod)/i],
    ["Mac OS", /Mac OS ?(?<version>X [0-9\._]+)?/i],
    ["Android", /Android/i],
    ["Linux", /Linux|X11|BSD|GNU/i],
  ];
}

class FakeUAData {
  constructor(data) {
    for (const key in data) {
      this[key] = data[key];
    }
  }

  async getHighEntropyValues(keys) {
    return this;
  }
}

export class UADataDetector extends GenericDetector {
  uaData = navigator.userAgentData;

  constructor(fakeData) {
    super();
    if (fakeData) {
      this.uaData = new FakeUAData(fakeData);
    }
  }

  async os(os = new OS()) {
    if (!this.uaData?.platform) {
      return os;
    }

    os.name = this.uaData.platform;
    let platformVersion;

    try {
      ({ platformVersion } = await this.uaData.getHighEntropyValues([
        "platformVersion",
      ]));
    } catch {
      return os;
    }

    if (this.uaData.platform === "Windows") {
      let major = new Version(platformVersion).major;
      if (major >= 13) {
        os.version = "11";
      } else if (major >= 1) {
        os.version = "10";
      }
    }

    return os;
  }
}

class FakeTroubleshooting {
  constructor(data) {
    this.data = data;
  }

  async getData() {
    return this.data;
  }
}

export class TroubleshootingDetector extends GenericDetector {
  remote = new RemoteTroubleshooting();

  constructor(fakeData) {
    super();
    if (fakeData) {
      this.remote = new FakeTroubleshooting(fakeData);
    }
  }

  async browser(browser = new Browser()) {
    let { application: { name, version } = {} } = await this.remote.getData();
    if (name && version) {
      browser.mozilla = true;
      browser.brands = [name];
      browser.version = new Version(version);
    }
    return browser;
  }

  async os(os = new OS()) {
    let { application: { osVersion } = {} } = await this.remote.getData();
    const isWin11 = TroubleshootingDetector.windows11Regex.test(osVersion);
    if (isWin11) {
      os.name = "Windows";
      os.version = "11";
    }
    return os;
  }

  static windows11Regex = /^Windows_NT 10\.0 2[0-9]{4}$/i;
}

export default class BrowserDetect {
  constructor(fakeUA, fakeUAData, fakeTroubleshooting) {
    this.uaDetector = new UADetector(fakeUA);
    this.uaDataDetector = new UADataDetector(fakeUAData);
    this.troubleshootingDetector = new TroubleshootingDetector(
      fakeTroubleshooting
    );
  }

  async getBrowser() {
    let browser = await this.uaDetector.browser();
    let os = await this.uaDetector.os();
    if (browser.mozilla && !os.mobile) {
      browser = await this.troubleshootingDetector.browser(browser);
    }
    return browser;
  }

  async getOS() {
    let os = await this.uaDetector.os();
    if (os.name === "Windows" && os.version === "10") {
      // could be windows 11
      let browser = await this.uaDetector.browser();
      if (browser.mozilla && !os.mobile) {
        os = await this.troubleshootingDetector.os(os);
      } else {
        os = await this.uaDataDetector.os(os);
      }
    }
    return os;
  }
}
