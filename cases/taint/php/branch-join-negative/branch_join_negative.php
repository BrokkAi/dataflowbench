<?php
function dfb_source(): string { // DFB-SOURCE: branch-join-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: branch-join-sink

function run(bool $overwrite): void {
    $value = dfb_source();
    if ($overwrite) {
        $value = "clean";
    } else {
        $value = "clean";
    }
    // DFB-WITNESS: branch-join-value
    dfb_sink($value);
}
