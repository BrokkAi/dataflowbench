<?php
function dfb_source(): string { // DFB-SOURCE: context-pair-depth2-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: context-pair-depth2-sink

function helper(string $value): string { // DFB-WITNESS: context-pair-depth2-helper
    return $value;
}

function wrapper(string $value): string { // DFB-WITNESS: context-pair-depth2-wrapper
    return helper($value);
}

function outerTainted(): string
{
    return wrapper(dfb_source());
}

function outerClean(): string
{
    return wrapper("clean");
}

function run(): void {
    $tainted = outerTainted();
    $clean = outerClean();
    dfb_sink($tainted);
}
