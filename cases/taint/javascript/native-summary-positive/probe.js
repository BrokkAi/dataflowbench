const child_process = require("child_process");

function run() {
  const value = process.env.DFB_INPUT; // DFB-SOURCE: native-summary-input
  const encoded = Buffer.from(value).toString("base64");
  const decoded = Buffer.from(encoded, "base64").toString();
  child_process.execSync(decoded); // DFB-SINK: native-summary-sink
}

run();
