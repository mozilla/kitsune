import {EventEmitter} from 'events';

const CHANGE_EVENT = 'change';

/**
 * Base class for Flux-style data stores.
 */
export default class BaseStore extends EventEmitter {
  /**
   * Fire a change event for this store.
   */
  emitChange() {
    this.emit(CHANGE_EVENT);
  }

  /**
   * Add change listener.
   * @param {Function} callback Function to call when any thing changes in this store.
   */
  addChangeListener(callback) {
    this.on(CHANGE_EVENT, callback);
  }

  /**
   * Remove a listner from this store.
   * @param {Function} callback The callback that was passed to {@link addChangeListener}.
   */
  removeChangeListener(callback) {
    this.removeListener(CHANGE_EVENT, callback);
  }
}
