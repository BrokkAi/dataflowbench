<?php
function dfb_source(): string { // DFB-SOURCE: closure-capture-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: closure-capture-sink

function makeReporter(): \Closure
{
    $tainted = dfb_source(); // DFB-WITNESS: closure-capture-bind
    $captured = "clean";
    return function () use ($captured): void {
        dfb_sink($captured);
    };
}

function run(): void {
    $reporter = makeReporter();
    $reporter();
}
