const child_process = require("child_process");

function run() {
  const ignored = process.env.DFB_INPUT; // DFB-SOURCE: native-source-sink-input
  const value = "printf constant";
  child_process.execSync(value); // DFB-SINK: native-source-sink-sink
  return ignored;
}

run();
