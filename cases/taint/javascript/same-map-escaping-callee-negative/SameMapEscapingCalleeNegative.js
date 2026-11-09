function dfb_source() { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
function dfb_sink(value) { console.log(value); } // DFB-SINK: issue303-sink
function write_source(values) {
    values.set("private", dfb_source()); // DFB-WITNESS: issue303-callee-store
}
function run(args) {
    const values = new Map([["payload", "clean"]]);
    write_source(values); // DFB-WITNESS: issue303-invoke
    dfb_sink(values.get("payload")); // DFB-WITNESS: issue303-read
}
run(process.argv.slice(2));
