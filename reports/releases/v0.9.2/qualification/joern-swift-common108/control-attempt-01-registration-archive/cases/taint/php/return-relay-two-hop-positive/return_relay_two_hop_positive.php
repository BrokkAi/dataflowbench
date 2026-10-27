<?php
function dfb_source(): string { // DFB-SOURCE: return-two-hop-input
    return "tainted";
}

function firstRelay(string $value): string { // DFB-WITNESS: return-two-hop-first
    return $value;
}

function secondRelay(string $value): string { // DFB-WITNESS: return-two-hop-second
    return firstRelay($value);
}

function dfb_sink(string $value): void {} // DFB-SINK: return-two-hop-sink

function run(): void {
    $result = secondRelay(dfb_source());
    dfb_sink($result);
}
