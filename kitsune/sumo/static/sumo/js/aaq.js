import BrowserDetect from "./browserdetect";

/*
 * Prepopulate system info in AAQ form
 */

(function($) {
  "use strict";

  function AAQSystemInfo($form) {
    AAQSystemInfo.prototype.init.call(this, $form);
  }

  AAQSystemInfo.prototype = {
    init: function($form) {
      var self = this,
        $input;

      // Autofill the user agent
      $form.find('input[name="useragent"]').val(navigator.userAgent);

      // Only guess at OS, FF version, plugins if we are on the desktop
      // asking a firefox desktop question (or s/desktop/mobile/).
      if (
        (BrowserDetect.browser === "fx" && self.isDesktopFF()) ||
        (BrowserDetect.browser === "m" && self.isMobileFF()) ||
        (BrowserDetect.browser === "fxios" && self.isFirefoxForIOS())
      ) {
        $input = $form.find('input[name="os"]');
        if (!$input.val()) {
          $input.val(self.getOS());
        }
        $input = $form.find('input[name="ff_version"]');
        if (!$input.val()) {
          $input.val(self.getFirefoxVersion());
        }
        $input = $form.find('input[name="device"]');
        if (!$input.val()) {
          $input.val(self.getDevice());
        }
        $input = $form.find('textarea[name="plugins"]');
        if (!$input.val()) {
          $input.val(self.getPlugins());
        }
      } else {
        $form.find('li.system-details-info').hide();
      }

      self.getTroubleshootingInfo();
    },
    getOS: function() {
      // Returns a string representing the user's operating system
      var os = [
          ["Android", /Android/i],
          ["Maemo", /Maemo/i],
          ["Windows 3.11", /Win16/i],
          ["Windows 95", /(Windows 95)|(Win95)|(Windows_95)/i],
          ["Windows 98", /(Windows 98)|(Win98)/i],
          ["Windows 2000", /(Windows NT 5.0)|(Windows 2000)/i],
          ["Windows XP", /(Windows NT 5.1)|(Windows XP)/i],
          ["Windows Server 2003", /(Windows NT 5.2)/i],
          ["Windows Vista", /(Windows NT 6.0)/i],
          ["Windows 7", /(Windows NT 6.1)/i],
          ["Windows 8", /(Windows NT 6.2)/i],
          ["Windows 8.1", /(Windows NT 6.3)/i],
          ["Windows 10", /(Windows NT 6.4)|(Windows NT 10.0)/i],
          ["Windows NT 4.0", /(Windows NT 4.0)|(WinNT4.0)/i],
          ["Windows ME", /Windows ME/i],
          ["Windows", /(Windows)|(WinNT)/i],
          ["OpenBSD", /OpenBSD/i],
          ["SunOS", /SunOS/i],
          ["Linux", /(Linux)|(X11)/i],
          ["iOS", /(iPhone)|(iPad)|(iPod touch)/i],
          ["Mac OS X 10.4", /(Mac OS X 10.4)/i],
          ["Mac OS X 10.5", /(Mac OS X 10.5)/i],
          ["Mac OS X 10.6", /(Mac OS X 10.6)/i],
          ["Mac OS X 10.7", /(Mac OS X 10.7)/i],
          ["Mac OS X 10.8", /(Mac OS X 10.8)/i],
          ["Mac OS X 10.9", /(Mac OS X 10.9)/i],
          ["Mac OS X 10.10", /(Mac OS X 10.10)/i],
          ["Mac OS", /(Mac_PowerPC)|(Macintosh)/i],
          ["QNX", /QNX/i],
          ["BeOS", /BeOS/i],
          ["OS/2", /OS\/2/i]
        ],
        ua = navigator.userAgent,
        i,
        l;
      for (i = 0, l = os.length; i < l; i++) {
        if (os[i][1].test(ua)) {
          return os[i][0];
        }
      }
      return navigator.oscpu || "";
    },
    getPlugins: function() {
      // Returns wiki markup for the list of plugins
      var plugins = [],
        i,
        d;
      for (i = 0; i < navigator.plugins.length; i++) {
        d = navigator.plugins[i].description.replace(/<[^>]+>/gi, "");
        if (plugins.indexOf(d) === -1) {
          plugins.push(d);
        }
      }
      if (plugins.length > 0) {
        plugins = "* " + plugins.join("\n* ");
      } else {
        plugins = "";
      }
      return plugins;
    },
    getFirefoxVersion: function() {
      // Returns a string with the version of Firefox
      var version = /Firefox\/(\S+)/i.exec(navigator.userAgent);
      if (version) {
        return version[1];
      }
      version = /FxiOS\/(\S+)/i.exec(navigator.userAgent);
      if (version) {
        return version[1];
      }
      return "";
    },
    getDevice: function() {
      // Returns a string with the device being used
      var device = /\(Mobile; (.+); .+\)/i.exec(navigator.userAgent);
      if (device) {
        return device[1];
      }
      device = /\((iPad|iPhone|iPod touch);/.exec(navigator.userAgent);
      if (device) {
        return device[1];
      }
      return "";
    },
    isDesktopFF: function() {
      // Is the question for FF on the desktop?
      return document.location.pathname.indexOf("desktop") >= 0 ||
        document.location.pathname.indexOf("firefox-enterprise") >= 0;
    },
    isMobileFF: function() {
      // Is the question for FF on mobile?
      return document.location.pathname.indexOf("mobile") >= 0
    },
    isFirefoxForIOS: function() {
      // Is the question for Firefox for iOS?
      return document.location.pathname.indexOf("ios") >= 0;
    },
    getTroubleshootingInfo: function(addEvent) {
      var self = this;
      var browserData;

      if (addEvent === undefined) {
        addEvent = true;
      }

      // If the troubleshoot input exists, try to get the data.
      if ($("#id_troubleshooting").length === 0) {
        // No troubleshooting form, so no point in trying to get the data.
        return;
      }

      // First we try to use the builtin API:
      remoteTroubleshooting.available(function(yesno) {
        if (yesno) {
          remoteTroubleshooting.getData(function(data) {
            browserData = data;
          });

          $("#share-data").click(function(e) {
            // The user must click button to save the data.
            e.preventDefault();
            handleData(browserData);
            return false;
          });
        } else {
          $("#share-data").click(function (e) {
            e.preventDefault();
            $("#troubleshooting-button").hide();
            $("#troubleshooting-manual").show();
            $("#troubleshooting-field").show();
            return false;
          });
        }
      });

      // Handle the troubleshooting JSON data.
      function handleData(data) {
        var modifiedPreferences = data.modifiedPreferences;
        data.modifiedPreferences = {};
        for (var key in modifiedPreferences) {
          if (key.indexOf("print.") !== 0) {
            data.modifiedPreferences[key] = modifiedPreferences[key];
          }
        }
        // The last two parameters cause this to pretty print,
        // in case anyone looks at it.
        data = JSON.stringify(data, null, "  ");
        $("#id_troubleshooting").val(data);
        $("#troubleshooting-field").show();
      }
    }
  };

  window.AAQSystemInfo = AAQSystemInfo;
})(jQuery);
