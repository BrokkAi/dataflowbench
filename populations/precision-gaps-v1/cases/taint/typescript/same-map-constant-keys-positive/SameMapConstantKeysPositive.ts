function dfb_source(): string { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
function dfb_sink(value: string): void { console.log(value); } // DFB-SINK: issue303-sink
function run(args: string[]): void {
    const values = new Map<string, string>([["payload", "clean"], ["tainted", "clean"]]);
    values.set("tainted", dfb_source()); // DFB-WITNESS: issue303-store
    dfb_sink((values.get("tainted") ?? "missing")); // DFB-WITNESS: issue303-read
}
const runtimeArgs = (globalThis as unknown as { process?: { argv: string[] } }).process?.argv.slice(2) ?? [];
run(runtimeArgs);
