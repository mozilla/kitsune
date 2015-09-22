import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';
import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import {actionTypes, questionEditState} from '../constants/AAQConstants.es6.js';

let troubleshootingInfo = {
  optIn: false,
  data: null,
  available: false,
};

class _TroubleshootingDataStore extends BaseStore {
  getData() {
    if (troubleshootingInfo.optIn) {
      return troubleshootingInfo.data;
    } else {
      return null;
    }
  }

  getOptedIn() {
    return troubleshootingInfo.optIn;
  }

  getAvailable() {
    return troubleshootingInfo.available;
  }

  getAll() {
    return {
      data: this.getData(),
      optIn: this.getOptedIn(),
      available: this.getAvailable(),
    };
  }
}

// Stores are singletons.
const TroubleshootingDataStore = new _TroubleshootingDataStore();

TroubleshootingDataStore.dispatchToken = Dispatcher.register((action) => {
  switch (action.type) {
    case actionTypes.TROUBLESHOOTING_OPT_IN:
      troubleshootingInfo.optIn = true;
      TroubleshootingDataStore.emitChange();
      break;

    case actionTypes.TROUBLESHOOTING_OPT_OUT:
      troubleshootingInfo.optIn = false;
      TroubleshootingDataStore.emitChange();
      break;

    case actionTypes.TROUBLESHOOTING_SET_DATA:
      troubleshootingInfo.data = action.data;
      TroubleshootingDataStore.emitChange();
      break;

    case actionTypes.TROUBLESHOOTING_AVAILABLE:
      troubleshootingInfo.available = action.available;
      TroubleshootingDataStore.emitChange();
      break;

    default:
      // do nothing
  }
});

export default TroubleshootingDataStore;
