import { apiFetch } from "sumo/js/utils/fetch";

let queue = null;

async function flush(state) {
  state.inFlight = true;
  let sending = state.latest;
  while (sending !== null) {
    try {
      await apiFetch(state.endpoint, {
        method: "POST",
        data: { preference: sending, owner: state.owner },
        keepalive: true,
      });
    } catch (error) {
      // A failed save leaves the choice on the page and is not retried.
      if (error?.response?.status === 409) {
        state.stopped = true;
      }
    }
    // No await between this read and the loop exit, so a choice made meanwhile is never lost.
    sending = !state.stopped && state.latest !== sending ? state.latest : null;
  }
  state.inFlight = false;
}

export function savePreference(preference) {
  const root = document.documentElement;
  const endpoint = root.getAttribute("data-theme-endpoint");
  const owner = root.getAttribute("data-theme-owner");
  if (owner === null || !endpoint) {
    return;
  }

  // Keyed so a page re-prepared in tests doesn't inherit the old in-flight request or 409 stop.
  if (!queue || queue.endpoint !== endpoint || queue.owner !== owner) {
    queue = { endpoint, owner, inFlight: false, latest: null, stopped: false };
  }
  queue.latest = preference;
  if (!queue.inFlight && !queue.stopped) {
    flush(queue);
  }
}
