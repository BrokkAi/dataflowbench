<?php
function dfb_source(): string { // DFB-SOURCE: infeasible-branch-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: infeasible-branch-sink

function run(): void {
    $value = "clean";
    if (true) {
        $value = dfb_source(); // DFB-WITNESS: feasible-tainted-branch
    }
    dfb_sink($value);
}
