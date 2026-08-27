const child_process = require("child_process");
const path = require("path");

function run() {
  const value = process.env.DFB_INPUT; // DFB-SOURCE: native-propagator-input
  const command = path.join("/usr/local/dfb", value);
  child_process.execSync(command); // DFB-SINK: native-propagator-sink
}

run();
