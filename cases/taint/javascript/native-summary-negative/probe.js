const child_process = require("child_process");

function run() {
  const ignored = process.env.DFB_INPUT; // DFB-SOURCE: native-summary-input
  const encoded = Buffer.from("printf constant").toString("base64");
  const decoded = Buffer.from(encoded, "base64").toString();
  child_process.execSync(decoded); // DFB-SINK: native-summary-sink
  return ignored;
}

run();
