function dfb_source() { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
function dfb_sink(value) { console.log(value); } // DFB-SINK: issue303-sink
function run(args) {
    const suffix = args.length > 0 ? args[0] : "payload";
    const key = "private:" + suffix;
    const values = new Map([["payload", "clean"]]);
    values.set(key, dfb_source()); // DFB-WITNESS: issue303-store
    dfb_sink(values.get("payload")); // DFB-WITNESS: issue303-read
}
run(process.argv.slice(2));
