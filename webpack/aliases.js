const path = require("path");

module.exports = {
  protocol: "@mozilla-protocol/core/protocol",
  sumo: path.resolve(__dirname, "../kitsune/sumo/static/sumo"),
  community: path.resolve(__dirname, "../kitsune/community/static/community"),
  kpi: path.resolve(__dirname, "../kitsune/kpi/static/kpi"),
};
