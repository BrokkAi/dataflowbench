const child_process = require("child_process");
const path = require("path");

function run() {
  const value = process.env.DFB_INPUT; // DFB-SOURCE: native-propagator-input
  const unused = path.join("/usr/local/dfb", value);
  const command = path.join("/usr/local/dfb", "constant");
  child_process.execSync(command); // DFB-SINK: native-propagator-sink
  return unused;
}

run();
