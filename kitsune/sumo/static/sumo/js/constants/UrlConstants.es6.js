import constantMap from "../../../sumo/js/utils/constantMap.es6.js";

export const actionTypes = constantMap(["UPDATE_PATH", "UPDATE_PATH_DEFAULTS"]);

export const pathStructure = ["locale", "model", "action", "product", "topic"];

export default {
  actionTypes,
  pathStructure,
};
