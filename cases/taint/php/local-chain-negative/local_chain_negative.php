<?php
function dfb_source(): string { // DFB-SOURCE: local-chain-negative-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: local-chain-negative-sink

function run(): void {
    $first = dfb_source();
    $second = $first; // DFB-WITNESS: local-chain-negative-second
    $third = $second; // DFB-WITNESS: local-chain-negative-third
    dfb_sink("clean");
}
