<?php
function dfb_source(): string { // DFB-SOURCE: trivial-overhead-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: trivial-overhead-sink

function run(): void {
    dfb_source();
    dfb_sink("clean");
}
