<?php
const DFB_FACTOR = 7;
define("DFB_LIMIT", 200);

function dfb_source(): string { // DFB-SOURCE: folded-local-constant-source
    return "tainted";
}

function dfb_sink(string $value): void { // DFB-SINK: folded-local-constant-sink
    echo $value, PHP_EOL;
}

function run_case(): void {
    $num = 100;
    $limit = DFB_LIMIT;
    $value = ((DFB_FACTOR * 42) - $num > $limit)
        ? "safe"
        : dfb_source(); // DFB-WITNESS: folded-local-constant-source-selected
    dfb_sink($value);
}

run_case();
