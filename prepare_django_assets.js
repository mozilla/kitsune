const util = require('util');
const cpx = require("cpx");
const fs = require('fs');

let rawdata = fs.readFileSync('package.json');
let packageJson = JSON.parse(rawdata);

Object.keys(packageJson.dependencies).forEach(function (packageName) {
  cpx.copy(
    util.format("node_modules/%s/**", packageName),
    util.format("assets/%s", packageName),
    function(err){
      if(err) {
        console.log(util.format("cpx error for %s: %s", packageName, err));
        process.exit(1);
      } else {
        console.log(util.format("copied %s to assets", packageName));
      }
    }
  );
});
