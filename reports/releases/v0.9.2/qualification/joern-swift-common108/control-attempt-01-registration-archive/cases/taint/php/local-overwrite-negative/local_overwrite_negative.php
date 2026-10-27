<?php
function dfb_source(): string { // DFB-SOURCE: local-overwrite-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: local-overwrite-sink

function run(): void {
    $value = dfb_source();
    $value = "clean"; // DFB-KILL: local-overwrite-clean
    dfb_sink($value);
}
