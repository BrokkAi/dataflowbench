const child_process = require("child_process");

function main() {
  const value = process.argv[2]; // DFB-SOURCE: native-entrypoint-input
  child_process.execSync(value); // DFB-SINK: native-entrypoint-sink
}

main();
