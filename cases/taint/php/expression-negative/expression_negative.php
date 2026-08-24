<?php
function dfb_source(): int { // DFB-SOURCE: expression-negative-input
    return 4;
}

function dfb_sink(int $value): void {} // DFB-SINK: expression-negative-sink

function run(): void {
    $value = dfb_source();
    $computed = ($value * 3) + 7; // DFB-WITNESS: expression-negative-computed
    dfb_sink(7);
}
