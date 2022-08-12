import { expect } from "chai";

import BrowserDetect, { Version } from "sumo/js/browserdetect";

describe("BrowserDetect", () => {
  const cases = [
    {
      description: "Windows 11, Firefox with alpha label",
      ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
      application: {
        name: "Firefox",
        version: "98.0a1",
        osVersion: "Windows_NT 10.0 22000",
      },
      browser: {
        mozilla: true,
        brands: ["Firefox"],
        version: {
          major: 98,
          minor: 0,
          patch: undefined,
          label: "a1",
        },
      },
      os: {
        name: "Windows",
        version: "11",
      },
    },
    {
      description: "Windows 11, Firefox no remote troubleshooting",
      ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
      browser: {
        mozilla: true,
        brands: ["Firefox"],
        version: {
          major: 100,
          minor: 0,
          patch: undefined,
          label: undefined,
        },
      },
      os: {
        name: "Windows",
        version: "10",
      },
    },
    {
      description: "Windows 10, Firefox",
      ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
      application: {
        name: "Firefox",
        version: "96.0.1",
        osVersion: "Windows_NT 10.0 19044",
      },
      browser: {
        mozilla: true,
        brands: ["Firefox"],
        version: {
          major: 96,
          minor: 0,
          patch: 1,
          label: undefined,
        },
      },
      os: {
        name: "Windows",
        version: "10",
      },
    },
    {
      description: "Windows 7, Firefox",
      ua: "Mozilla/5.0 (Windows NT 6.1; rv:95.0) Gecko/20100101 Firefox/95.0",
      application: {
        name: "Firefox",
        version: "95.0.2",
        osVersion: "Windows_NT 6.1 7601",
      },
      browser: {
        mozilla: true,
        brands: ["Firefox"],
        version: {
          major: 95,
          minor: 0,
          patch: 2,
          label: undefined,
        },
      },
      os: {
        name: "Windows",
        version: "7",
      },
    },
    {
      description: "Mac OS, Firefox with patch version",
      ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
      application: {
        name: "Firefox",
        version: "95.0.2",
        osVersion:
          "Darwin 20.6.0 Darwin Kernel Version 20.6.0: Mon Aug 30 06:12:21 PDT 2021;",
      },
      browser: {
        mozilla: true,
        brands: ["Firefox"],
        version: {
          major: 95,
          minor: 0,
          patch: 2,
          label: undefined,
        },
      },
      os: {
        name: "Mac OS",
        version: "x 10.15",
      },
    },
    {
      description: "Linux, Firefox",
      ua: "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
      application: {
        name: "Firefox",
        version: "95.0",
        osVersion:
          "Linux 5.15.7-arch1-1 #1 SMP PREEMPT Wed, 08 Dec 2021 14:33:16 +0000",
      },
      browser: {
        mozilla: true,
        brands: ["Firefox"],
        version: {
          major: 95,
          minor: 0,
          patch: undefined,
          label: undefined,
        },
      },
      os: {
        name: "Linux",
        version: undefined,
      },
    },
    {
      description: "Android, Firefox",
      ua: "Mozilla/5.0 (Android 12; Mobile; rv:98.0) Gecko/98.0 Firefox/98.0",
      browser: {
        mozilla: true,
        brands: ["Firefox", "Firefox Focus"],
        version: {
          major: 98,
          minor: 0,
          patch: undefined,
          label: undefined,
        },
      },
      os: {
        name: "Android",
        version: undefined,
      },
    },
    {
      description: "Android, Firefox Focus",
      ua: "Mozilla/5.0 (Android 12; Mobile; rv:95.0) Gecko/95.0 Firefox/95.0",
      browser: {
        mozilla: true,
        brands: ["Firefox", "Firefox Focus"],
        version: {
          major: 95,
          minor: 0,
          patch: undefined,
          label: undefined,
        },
      },
      os: {
        name: "Android",
        version: undefined,
      },
    },
    {
      description: "iOS, Firefox",
      ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/40.2 Mobile/15E148 Safari/605.1.15",
      browser: {
        mozilla: true,
        brands: ["Firefox", "Firefox Focus"],
        version: {
          major: 40,
          minor: 2,
          patch: undefined,
          label: undefined,
        },
      },
      os: {
        name: "iOS",
        version: undefined,
      },
    },
    {
      description: "iOS, Firefox Focus",
      ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/7.0.4 Mobile/16B91 Safari/605.1.15",
      browser: {
        mozilla: true,
        brands: ["Firefox", "Firefox Focus"],
        version: {
          major: 7,
          minor: 0,
          patch: 4,
          label: undefined,
        },
      },
      os: {
        name: "iOS",
        version: undefined,
      },
    },
    {
      description: "iPadOS, Firefox", // bug: https://github.com/mozilla-mobile/firefox-ios/issues/6620
      ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Mac OS",
        version: "x 10_15_4",
      },
    },
    {
      description: "iPadOS, Firefox Focus", // bug: https://github.com/mozilla-mobile/firefox-ios/issues/6620
      ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Mac OS",
        version: "x 10_15_6",
      },
    },
    {
      description: "Windows 11, Edge",
      ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62",
      hints: {
        platform: "Windows",
        platformVersion: "14.0.0",
      },
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Windows",
        version: "11",
      },
    },
    {
      description: "Windows 11, Edge no UA hints",
      ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Windows",
        version: "10",
      },
    },
    {
      description: "Windows 10, Edge",
      ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62",
      hints: {
        platform: "Windows",
        platformVersion: "10.0.0",
      },
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Windows",
        version: "10",
      },
    },
    {
      description: "Windows 7, Edge",
      ua: "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62",
      hints: {
        platform: "Windows",
        platformVersion: "0.0.0",
      },
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Windows",
        version: "7",
      },
    },
    {
      description: "Mac OS, Safari",
      ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Mac OS",
        version: "x 10_15_7",
      },
    },
    {
      description: "Linux, Chromium",
      ua: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Linux",
        version: undefined,
      },
    },
    {
      description: "Android, Chrome",
      ua: "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.87 Mobile Safari/537.36",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Android",
        version: undefined,
      },
    },
    {
      description: "iOS, Safari",
      ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "iOS",
        version: undefined,
      },
    },
    {
      description: "iPadOS, Safari",
      ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
      browser: {
        mozilla: false,
        brands: undefined,
        version: undefined,
      },
      os: {
        name: "Mac OS",
        version: "x 10_15_6",
      },
    },
  ];

  for (const { description, ua, application, hints, browser, os } of cases) {
    it(`handles ${description}`, async () => {
      const detect = new BrowserDetect(ua, hints, { application });
      let detectedBrowser = await detect.getBrowser();
      let detectedOS = await detect.getOS();
      expect(detectedBrowser).to.deep.equal(browser);
      expect(detectedOS).to.deep.equal(os);
    });
  }

  describe("Version", () => {
    describe("toString", () => {
      const stringCases = [
        {
          input: "1",
          empty: "1",
          major: "1",
          minor: "1.0",
          patch: "1.0.0",
          label: "1.0.0",
        },
        {
          input: "1.2",
          empty: "1.2",
          major: "1",
          minor: "1.2",
          patch: "1.2.0",
          label: "1.2.0",
        },
        {
          input: "1.2.3",
          empty: "1.2.3",
          major: "1",
          minor: "1.2",
          patch: "1.2.3",
          label: "1.2.3",
        },
        {
          input: "1.2.3.4",
          empty: "1.2.3",
          major: "1",
          minor: "1.2",
          patch: "1.2.3",
          label: "1.2.3",
        },
        {
          input: "1.2.3a1",
          empty: "1.2.3a1",
          major: "1",
          minor: "1.2",
          patch: "1.2.3",
          label: "1.2.3a1",
        },
        {
          input: "1.2.3z1",
          empty: "1.2.3",
          major: "1",
          minor: "1.2",
          patch: "1.2.3",
          label: "1.2.3",
        },
        {
          input: "foobar",
          empty: "",
          major: "0",
          minor: "0.0",
          patch: "0.0.0",
          label: "0.0.0",
        },
      ];

      for (const { input, empty, major, minor, patch, label } of stringCases) {
        it(`handles ${input}`, () => {
          let version = new Version(input);
          expect(version.toString()).to.equal(empty);
          expect(version.toString("major")).to.equal(major);
          expect(version.toString("minor")).to.equal(minor);
          expect(version.toString("patch")).to.equal(patch);
          expect(version.toString("label")).to.equal(label);
        });
      }
    });
  });
});
