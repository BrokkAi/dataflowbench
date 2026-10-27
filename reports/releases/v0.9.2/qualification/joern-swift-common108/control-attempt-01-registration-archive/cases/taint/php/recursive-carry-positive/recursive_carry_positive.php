<?php
function dfb_source(): string { // DFB-SOURCE: recursive-carry-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: recursive-carry-sink

function carry(string $value, int $depth): string { // DFB-WITNESS: recursive-carry-step
    if ($depth === 0) {
        return $value;
    }
    return carry($value, $depth - 1);
}

function run(): void {
    dfb_sink(carry(dfb_source(), 5));
}
