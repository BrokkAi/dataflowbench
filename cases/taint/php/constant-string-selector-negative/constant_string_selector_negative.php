<?php
function dfb_source(): string {
    return "source-one"; // DFB-SOURCE: constant-selector-input
}

function dfb_sink(string $value): void { // DFB-SINK: constant-selector-sink
    echo $value, PHP_EOL;
}

$selector = "ABC"[1];
$value = match ($selector) {
    "C" => dfb_source(), // DFB-WITNESS: constant-selector-source-arm
    "B" => "safe",
    default => "safe",
};
dfb_sink($value);
