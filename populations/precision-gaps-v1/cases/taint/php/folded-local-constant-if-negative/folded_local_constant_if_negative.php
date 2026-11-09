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
    $num = 86;
    $limit = DFB_LIMIT;
    $value = "safe";
    if ((DFB_FACTOR * 42) - $num > $limit) {
        $value = "safe";
    } else {
        $value = dfb_source();
    }
    dfb_sink($value);
}

run_case();
