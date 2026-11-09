<?php
function dfb_source(): string { // DFB-SOURCE: list-removal-index-shift-input
    return (string) getenv("DFB_INPUT");
}

function dfb_sink(string $value): void { // DFB-SINK: list-removal-index-shift-sink
    echo $value, "\n";
}

$values = [];
$values[] = "safe";
$values[] = dfb_source();
$values[] = "more-safe";
array_shift($values); // DFB-WITNESS: list-removal-index-shift-remove-first
dfb_sink($values[0]);
