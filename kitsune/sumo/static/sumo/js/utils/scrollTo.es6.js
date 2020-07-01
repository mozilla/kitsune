/* globals $:false */

var floatingHeaderOffset;
var floatingHeaderThreshold;

$(() => {
  /* Figure out the threshold and height of the floating header. This is
   * probably a bit slow since it triggers two to three reflows but it
   * shouldn't cause a flicker, and it only happens once when the pages
   * loads.
   */
  let $header = $("body > header");
  let $body = $("body");
  const scrollHeaderClass = "scroll-header";
  const hadScrollHeaderClass = $body.hasClass("scroll-header");

  $body.removeClass("scroll-header");
  floatingHeaderThreshold = $header.outerHeight();
  $body.addClass("scroll-header");
  floatingHeaderOffset = $header.height();

  if (!hadScrollHeaderClass) {
    $body.removeClass("scroll-header");
  }
});

export default function scrollTo(element, time = undefined) {
  let $element = $(element);
  let targetScrollPos = $element.offset().top;
  if (targetScrollPos > floatingHeaderThreshold) {
    targetScrollPos -= floatingHeaderOffset;
  }
  $("html").animate({ scrollTop: targetScrollPos }, time);
}
