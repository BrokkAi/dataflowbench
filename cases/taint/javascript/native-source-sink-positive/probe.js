const child_process = require("child_process");

function run() {
  const value = process.env.DFB_INPUT; // DFB-SOURCE: native-source-sink-input
  child_process.execSync(value); // DFB-SINK: native-source-sink-sink
}

run();
