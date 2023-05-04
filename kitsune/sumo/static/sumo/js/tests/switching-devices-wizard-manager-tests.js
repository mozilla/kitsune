import {expect} from 'chai';

import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";

describe('k', () => {
  describe('SwitchingDevicesWizardManager', () => {
    it('should be constructable', () => {
      expect(() => {
        new SwitchingDevicesWizardManager()
      }).to.not.throw();
    });
  });
});
