<?php
function dfb_source(): string { // DFB-SOURCE: map-iteration-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: map-iteration-sink

function run(): void {
    $records = [];
    $records["record"] = dfb_source(); // DFB-WITNESS: map-iteration-store
    foreach ($records as $key => $value) {
        dfb_sink($value);
    }
}
