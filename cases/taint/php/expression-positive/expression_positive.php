<?php
function dfb_source(): int { // DFB-SOURCE: expression-input
    return 4;
}

function dfb_sink(int $value): void {} // DFB-SINK: expression-sink

function run(): void {
    $value = dfb_source();
    $computed = ($value * 3) + 7; // DFB-WITNESS: expression-computed
    dfb_sink($computed);
}
