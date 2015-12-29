/* Re-export utils from the old-style global `k` library related to urls.
 * Includes sanity checks to make sure the right files were included.
 */

import '../main.js';

const names = [
  'getQueryParamsAsDict',
  'queryParamStringFromDict',
  'getPathAsDict',
  'pathStringFromDict',
];

for (let name of names) {
  if (window.k[name] === undefined) {
    throw new Error(`Shim validation error: Could not find ``k.${name}`` in global scope.`);
  }
}

export const getQueryParamsAsDict = window.k.getQueryParamsAsDict;
export const queryParamStringFromDict = window.k.queryParamStringFromDict;
export const getPathAsDict = window.k.getPathAsDict;
export const pathStringFromDict = window.k.pathStringFromDict;

