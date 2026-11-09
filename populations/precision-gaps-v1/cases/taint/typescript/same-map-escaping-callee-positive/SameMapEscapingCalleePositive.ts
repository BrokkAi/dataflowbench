function dfb_source(): string { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
function dfb_sink(value: string): void { console.log(value); } // DFB-SINK: issue303-sink
function write_source(values: Map<string, string>): void {
    values.set("payload", dfb_source()); // DFB-WITNESS: issue303-callee-store
}
function run(args: string[]): void {
    const values = new Map<string, string>([["payload", "clean"]]);
    write_source(values); // DFB-WITNESS: issue303-invoke
    dfb_sink((values.get("payload") ?? "missing")); // DFB-WITNESS: issue303-read
}
const runtimeArgs = (globalThis as unknown as { process?: { argv: string[] } }).process?.argv.slice(2) ?? [];
run(runtimeArgs);
