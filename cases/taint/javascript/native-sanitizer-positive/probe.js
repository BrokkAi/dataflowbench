const child_process = require("child_process");

function run() {
  const value = process.env.DFB_INPUT; // DFB-SOURCE: native-sanitizer-input
  const command = "printf " + value;
  child_process.execSync(command); // DFB-SINK: native-sanitizer-sink
}

run();
