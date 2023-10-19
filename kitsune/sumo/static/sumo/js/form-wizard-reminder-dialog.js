import reminderDialogStylesURL from "../scss/reminder-dialog.styles.scss";
import closeIconURL from "sumo/img/close.svg";
import successIconUrl from "sumo/img/success.svg";

const NEW_DEVICE_DOWNLOAD_URL = "https://mzl.la/newdevice";

const CALENDAR_FORMATS = Object.freeze({
  ICAL: 1,
  OUTLOOK: 2,
  GCAL: 3,
});

/**
 * The Form Wizard can open a ReminderDialog, which is a <dialog>
 * that lets the user create calendar events for themselves to
 * remind them download and install Firefox on their new devices.
 *
 * The ReminderDialog also lets users copy the download link to
 * their clipboard, in the event that they want to send themselves
 * the link via text or email.
 */
export class ReminderDialog extends HTMLDialogElement {
  #shadow = null;

  static get REMINDER_DAYS_IN_THE_FUTURE() {
    return 14;
  }

  static get markup() {
    return `
      <template>
        <div id="reminder-dialog-content">
          <div id="header" class="hbox">
            <h1 class="text-display-xxs">${gettext("Add to calendar")}</h1>
            <button id="close" class="mzp-c-button mzp-t-neutral" aria-label="${gettext("Close")}" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="close-reminder-dialog"><img src="${closeIconURL}" aria-hidden="true"/></button>
          </div>
          <div class="vbox">
            <div id="directions">${gettext("Save the download link to your calendar and finish the download whenever you’re ready.")}</div>
            <label for="choose-calendar">${gettext("Choose calendar")}</label>
            <div class="hbox">
              <select id="choose-calendar">
                <option value="gcal">Google Calendar</option>
                <option value="outlook">Outlook.com</option>
                <option value="ics">${gettext("Other calendar")}</option>
              </select>
              <button id="create-event" class="mzp-c-button mzp-t-product" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="create-calendar-event">${gettext("Save")}</button>
            </div>
            <hr>

            <div class="hbox">
              <span id="copy-link-message">${gettext("You can also access the link directly")}</span>
              <div id="copy-link-container" class="hbox">
                <button id="copy-link" class="mzp-c-button mzp-t-product mzp-t-secondary mzp-t-md" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="copy-link-to-clipboard-button">${gettext("Copy link")}</button>
                <span id="copied-message"><img src="${successIconUrl}" aria-hidden="true">${gettext("Copied!")}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    `;
  }

  static get styles() {
    let stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = reminderDialogStylesURL;
    return stylesheet;
  }

  constructor() {
    super();
    // We cannot create a shadow root on a <dialog>, so we'll create a root
    // <div> node and put the shadow root there instead.
    let rootNode = document.createElement("div");
    this.appendChild(rootNode);
    let shadow = rootNode.attachShadow({ mode: "open" });

    let parser = new DOMParser();
    let doc = parser.parseFromString(ReminderDialog.markup, "text/html");
    let template = doc.querySelector("template");
    shadow.append(ReminderDialog.styles, template.content.cloneNode(true));

    this.#shadow = shadow;
  }

  get shadow() {
    return this.#shadow;
  }

  connectedCallback() {
    let close = this.#shadow.querySelector("#close");
    close.addEventListener("click", this);

    let copyLinkButton = this.#shadow.querySelector("#copy-link");
    copyLinkButton.addEventListener("click", this);

    let createEventButton = this.#shadow.querySelector("#create-event");
    createEventButton.addEventListener("click", this);
  }

  handleEvent(event) {
    switch (event.currentTarget.id) {
      case "close": {
        this.close();
        break;
      }
      case "copy-link": {
        this.#copyLink();
        break;
      }
      case "create-event": {
        let calendarType = this.#shadow.querySelector("#choose-calendar").value;
        this.#createEvent(calendarType)
      }
    }
  }

  /**
   * This is a thin wrapper around window.location so that our automated
   * tests can easily stub this out and override it (since the test
   * framework we use gets upset when writing to window.location).
   *
   * @param {string} url
   *   The URL to send the browser to.
   */
  redirect(url) {
    window.location.href = url;
  }

  /**
   * Creates a summary and description string appropriate for a calendar
   * event for downloading and installing Firefox on a new device. This
   * will be translated to the current user's locale.
   *
   * @param {string} linkURL
   *   The URL that the event should provide to download Firefox.
   * @param {integer} format
   *   One of the CALENDAR_FORMATS constants.
   * @returns {object} result
   * @returns {string} result.summary
   *   The summary for the event.
   * @returns {string} result.description
   *   The description for the event, including the linkURL.
   */
  #generateEventSummaryAndDescription(linkURL, format) {
    let summary = gettext("Reminder to complete your Firefox backup");
    let description = interpolate(
      gettext("Your Firefox data has been successfully backed up.\n\nFollow this link to start your download: %s"),
      [linkURL]
    );

    if (format == CALENDAR_FORMATS.ICAL) {
      description = description.replace(/\n/g, "\\n");
    }

    return { summary, description };
  }

  /**
   * Generates start and end dates for the reminder. This function
   * will compute the correct start and end dates to produce an
   * "All Day" event for the given CALENDAR_FORMAT.
   *
   * @param {number} format
   *   One of the CALENDAR_FORMATS constants.
   * @returns {object} result
   * @returns {string} result.dtStart
   *   The start date of the event in a format appropriate for
   *   CALENDAR_FORMAT.
   * @returns {string} result.dtEnd
   *   The end date of the event in a format appropriate for
   *   CALENDAR_FORMAT.
   */
  #generateDTStartDTEnd(format) {
    let startDate = new Date();
    // Set the reminder for REMINDER_DAYS_IN_THE_FUTURE days in the future.
    startDate.setDate(startDate.getDate() + ReminderDialog.REMINDER_DAYS_IN_THE_FUTURE);

    let dtStart = this.#convertDateToDTFormat(format, startDate);

    // For Google Calendar, all-day events are encoded by not including
    // the time (handled by #generateDTStartDTEnd), and having the start
    // and end date match.
    // See https://stackoverflow.com/questions/37335415/link-to-add-all-day-event-to-google-calendar
    if (format == CALENDAR_FORMATS.GCAL) {
      return { dtStart, dtEnd: dtStart };
    }

    // For other formats, it's expected that the end date for an
    // "All Day" event be the next day.
    let endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + 1);
    let dtEnd = this.#convertDateToDTFormat(format, endDate);

    return { dtStart, dtEnd };
  }

  /**
   * Converts a DOM Date object into a string representation that
   * is compatible with the VEVENT format.
   *
   * @param {number} format
   *   One of the CALENDAR_FORMATS constants.
   * @param {Date} date
   *   The date to encode.
   * @returns {string}
   *   The VEVENT-compatible date, set at midnight, with no timezone
   *   information.
   */
  #convertDateToDTFormat(format, date) {
    let year = date.getFullYear().toString();

    // In all cases, months or days with single digits are expected to start
    // with a 0.

    // getMonth() is 0-indexed.
    let month = new String(date.getMonth() + 1).padStart(2, "0");
    let day = new String(date.getDate()).padStart(2, "0");

    switch (format) {
      case CALENDAR_FORMATS.OUTLOOK: {
        return `${year}-${month}-${day}`
      }
      case CALENDAR_FORMATS.ICAL:
        // Intentional fall-through
      case CALENDAR_FORMATS.GCAL: {
        return `${year}${month}${day}`
      }
      default: {
        throw new Error("#convertDateToDTFormat wasn't given a format for the date.");
      }
    }
  }

  /**
   * Generates a URL to download a .ics file that can be interpreted
   * by calendaring software to add an event to a calendar that reminds
   * the user to download and install Firefox on their new device.
   *
   * @returns {string}
   *   The blob URL for the .ics file download.
   */
  #generateICSFileDownload() {
    let now = this.#convertDateToDTFormat(CALENDAR_FORMATS.ICAL, new Date());
    let { dtStart, dtEnd } = this.#generateDTStartDTEnd(CALENDAR_FORMATS.ICAL);
    let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // mozilla/sumo#1503: The NEW_DEVICE_DOWNLOAD_URL should be replaced with
    // a link that attributes the download to an event from an ICS file.
    let { summary, description } = this.#generateEventSummaryAndDescription(NEW_DEVICE_DOWNLOAD_URL, CALENDAR_FORMATS.ICAL);

    // The random value here is not meant to be cryptographically
    // secure. The randomValue is used to create a unique UID for
    // the VEVENT.
    let randomValue = dtStart + Math.random();

    let icsFile = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML support.mozilla.org switching devices wizard V1.0//EN
BEGIN:VEVENT
UID:${randomValue}
DTSTAMP:${now}
DTSTART:${dtStart}
DTEND:${dtEnd}
SUMMARY:${summary}
DESCRIPTION:${description}
END:VEVENT
END:VCALENDAR
`;
    let blob = new Blob([icsFile], {type: "text/calendar;charset=utf-8;"});
    let blobURL = window.URL.createObjectURL(blob);
    return blobURL;
  }

  /**
   * Copies the NEW_DEVICE_DOWNLOAD_URL string to the clipboard,
   * and updates the UI to indicate that the copy was successful for
   * 5 seconds before returning to normal.
   */
  #copyLink() {
    let contentNode = this.#shadow.querySelector("#reminder-dialog-content");
    let copyLinkButton = this.#shadow.querySelector("#copy-link");
    navigator.clipboard.writeText(NEW_DEVICE_DOWNLOAD_URL);
    contentNode.toggleAttribute("data-copied", true);
    setTimeout(() => {
      contentNode.toggleAttribute("data-copied", false);
    }, 5000);
  }

  #createEvent(calendarType) {
    switch (calendarType) {
      case "gcal": {
        this.#openGCalTab();
        break;
      }
      case "outlook": {
        this.#openOutlookTab();
        break;
      }
      case "ics": {
        let icsDownload = this.#generateICSFileDownload();
        this.redirect(icsDownload);
        break;
      }
    }
  }

  #openGCalTab() {
    const GCAL_ENDPOINT = "https://calendar.google.com/calendar/render?";

    // mozilla/sumo#1503: The NEW_DEVICE_DOWNLOAD_URL should be replaced with
    // a link that attributes the download to an event from Google Calendar.
    let { summary, description } = this.#generateEventSummaryAndDescription(NEW_DEVICE_DOWNLOAD_URL, CALENDAR_FORMATS.GCAL);
    let { dtStart, dtEnd } = this.#generateDTStartDTEnd(CALENDAR_FORMATS.GCAL);
    let params = new URLSearchParams();
    params.set("action", "TEMPLATE");
    params.set("dates", `${dtStart}/${dtEnd}`);
    params.set("text", summary);
    params.set("details", description);
    window.open(GCAL_ENDPOINT + params);
  }

  #openOutlookTab() {
    const OUTLOOK_ENDPOINT = "https://outlook.live.com/calendar/0/deeplink/compose/?";

    // mozilla/sumo#1503: The NEW_DEVICE_DOWNLOAD_URL should be replaced with
    // a link that attributes the download to an event from Microsoft Outlook.
    let { summary, description } = this.#generateEventSummaryAndDescription(NEW_DEVICE_DOWNLOAD_URL, CALENDAR_FORMATS.OUTLOOK);
    let { dtStart, dtEnd } = this.#generateDTStartDTEnd(CALENDAR_FORMATS.OUTLOOK);
    let params = new URLSearchParams();

    // The arguments here were supplied by
    // https://interactiondesignfoundation.github.io/add-event-to-calendar-docs/services/outlook-web.html.
    params.set("body", description);
    params.set("subject", summary);
    params.set("startdt", dtStart);
    params.set("enddt", dtEnd);
    params.set("rru", "addevent");
    params.set("path", "/calendar/action/compose");
    params.set("allday", "true");
    window.open(OUTLOOK_ENDPOINT + params);
  }
}

customElements.define("reminder-dialog", ReminderDialog, {extends: "dialog"});