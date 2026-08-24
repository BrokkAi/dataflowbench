<?php
function dfb_source(): string { // DFB-SOURCE: argument-position-negative-input
    return "tainted";
}

function chooseFirst(string $first, string $second): string { // DFB-WITNESS: argument-position-negative-first
    return $first;
}

function dfb_sink(string $value): void {} // DFB-SINK: argument-position-negative-sink

function run(): void {
    $result = chooseFirst("clean", dfb_source());
    dfb_sink($result);
}
