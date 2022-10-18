export default class RemoteTroubleshooting {
  /**
   * Async method for retrieving remote-troubleshooting data.
   *
   * @param {integer} timeout - Timeout in milliseconds for calling
   * the callback with {} if the event hasn't yet gotten dispatched.
   * Defaults to 1000 ms (aka 1 second).
   *
   * @returns {object} with data in it or {}
   */
  async getData(timeout = 1000) {
    // If we've already gotten the data, return that.
    if (this.data) {
      return this.data;
    }

    // Listen to the WebChannelMessageToContent event and handle
    // incoming remote-troubleshooting messages.
    const dataPromise = new Promise((resolve, reject) => {
      window.addEventListener("WebChannelMessageToContent", (e) => {
        if (e.detail.id === "remote-troubleshooting") {
          let data = e.detail.message;
          if (data) {
            return resolve(data);
          }
        }
        reject();
      });
    });

    const timeoutPromise = new Promise((resolve, reject) => {
      window.setTimeout(() => reject(), timeout);
    });

    // Create the remote-troubleshooting event requesting data and
    // kick it off.
    const request = new window.CustomEvent("WebChannelMessageToChrome", {
      detail: JSON.stringify({
        id: "remote-troubleshooting",
        message: {
          command: "request",
        },
      }),
    });
    window.dispatchEvent(request);

    try {
      this.data = await Promise.race([dataPromise, timeoutPromise]);
    } catch {
      this.data = {};
    }

    return this.data;
  }
}
