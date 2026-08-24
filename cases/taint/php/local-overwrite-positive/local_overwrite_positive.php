<?php
function dfb_source(): string { // DFB-SOURCE: local-overwrite-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: local-overwrite-sink

function run(): void {
    $value = dfb_source();
    $value = $value; // DFB-WITNESS: local-overwrite-preserved
    dfb_sink($value);
}
