<?php
function dfb_source(): int { // DFB-SOURCE: loop-carried-input
    return 1;
}

function dfb_sink(int $value): void {} // DFB-SINK: loop-carried-sink

function run(): void {
    $value = dfb_source();
    for ($iteration = 0; $iteration < 3; $iteration++) {
        $value = 0; // DFB-WITNESS: loop-carried-value
    }
    dfb_sink($value);
}
