<?php
function dfb_source(): string { // DFB-SOURCE: local-chain-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: local-chain-sink

function run(): void {
    $first = dfb_source();
    $second = $first; // DFB-WITNESS: local-chain-second
    $third = $second; // DFB-WITNESS: local-chain-third
    dfb_sink($third);
}
