<?php
function dfb_source(): string { // DFB-SOURCE: argument-position-input
    return "tainted";
}

function chooseFirst(string $first, string $second): string { // DFB-WITNESS: argument-position-first
    return $first;
}

function dfb_sink(string $value): void {} // DFB-SINK: argument-position-sink

function run(): void {
    $result = chooseFirst(dfb_source(), "clean");
    dfb_sink($result);
}
