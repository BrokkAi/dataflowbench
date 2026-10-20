const child_process = require("child_process");

function main() {
  const argument = process.argv[2]; // DFB-SOURCE: native-entrypoint-input
  const value = "printf constant";
  child_process.execSync(value); // DFB-SINK: native-entrypoint-sink
  return argument;
}

main();
