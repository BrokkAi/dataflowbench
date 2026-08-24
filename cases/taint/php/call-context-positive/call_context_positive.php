<?php
function dfb_source(): string { // DFB-SOURCE: call-context-input
    return "tainted";
}

function relay(string $value): string { // DFB-WITNESS: call-context-relay
    return $value;
}

function dfb_sink(string $value): void {} // DFB-SINK: call-context-sink

function run(): void {
    $tainted = relay(dfb_source());
    $clean = relay("clean");
    dfb_sink($tainted);
}
