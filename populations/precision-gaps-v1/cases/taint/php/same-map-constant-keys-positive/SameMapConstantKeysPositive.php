<?php
function dfb_source(): string { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
function dfb_sink(string $value): void { echo $value, PHP_EOL; } // DFB-SINK: issue303-sink
function run(array $args): void {
    $values = ["payload" => "clean", "tainted" => "clean"];
    $values["tainted"] = dfb_source(); // DFB-WITNESS: issue303-store
    dfb_sink($values["tainted"]); // DFB-WITNESS: issue303-read
}
run(array_slice($argv, 1));
