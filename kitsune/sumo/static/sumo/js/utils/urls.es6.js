/* Re-export utils from the old-style global `k` library related to urls.
 * Includes sanity checks to make sure the right files were included.
 */

import "../main.js";

const names = ["getQueryParamsAsDict", "queryParamStringFromDict"];

for (let name of names) {
  if (window.k[name] === undefined) {
    throw new Error(
      `Shim validation error: Could not find ``k.${name}`` in global scope.`
    );
  }
}

export const getQueryParamsAsDict = window.k.getQueryParamsAsDict;
export const queryParamStringFromDict = window.k.queryParamStringFromDict;

export function getPathAsDict(propertyNames) {
  var pathDict = {},
    pathArray = window.location.pathname.split("/").filter(Boolean);

  propertyNames.forEach(function (value, index) {
    pathDict[value] = pathArray[index];
  });

  return pathDict;
}

export function pathStringFromDict(pathDict) {
  var pathString = "";

  for (let key in pathDict) {
    if (pathDict[key]) {
      pathString += "/" + pathDict[key];
    }
  }

  return pathString;
}
