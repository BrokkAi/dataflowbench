<?php
function dfb_source(): string { // DFB-SOURCE: constant-selector-input
    return "source-one";
}

function dfb_sink(string $value): void { // DFB-SINK: constant-selector-sink
    echo $value, PHP_EOL;
}

$selector = "ABC"[2];
switch ($selector) {
    case "C":
        $value = dfb_source(); // DFB-WITNESS: constant-selector-source-arm
        break;
    case "B":
        $value = "safe";
        break;
    default:
        $value = "safe";
        break;
}
dfb_sink($value);
