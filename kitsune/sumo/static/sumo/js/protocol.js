import MzpBase from "protocol/js/base";
import MzpSupports from "protocol/js/supports";
import MzpUtils from "protocol/js/utils";
import "protocol/js/details";
import "protocol/js/footer";
import "protocol/js/menu";
import "protocol/js/modal";
import "protocol/js/navigation";
import "protocol/js/newsletter";
import "protocol/js/notification-bar";
import "protocol/js/lang-switcher";

// In webpack's CommonJS context, UMD modules don't set browser globals.
// Protocol checks window.MzpSupports before initializing JS-enhanced components,
// so we expose it manually. Also fix the matchMedia check: Protocol uses
// addListener() which was removed in Chrome 127+ (2024).
MzpSupports.matchMedia = typeof window.matchMedia !== 'undefined';
window.MzpSupports = MzpSupports;
window.MzpUtils = MzpUtils;

MzpBase.init();
