<?php
function dfb_source(): string { // DFB-SOURCE: return-one-hop-negative-input
    return "tainted";
}

function relay(string $value): string { // DFB-WITNESS: return-one-hop-negative-relay
    return $value;
}

function dfb_sink(string $value): void {} // DFB-SINK: return-one-hop-negative-sink

function run(): void {
    $result = relay(dfb_source());
    dfb_sink("clean");
}
