const child_process = require("child_process");

function run() {
  process.env.DFB_STORED = process.argv[2]; // DFB-SOURCE: native-persistence-input
  const value = process.env.DFB_STORED;
  child_process.execSync(value); // DFB-SINK: native-persistence-sink
}

run();
