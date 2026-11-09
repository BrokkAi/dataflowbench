<?php
function dfb_source(): string { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
function dfb_sink(string $value): void { echo $value, PHP_EOL; } // DFB-SINK: issue303-sink
function write_source(array &$values): void {
    $values["private"] = dfb_source(); // DFB-WITNESS: issue303-callee-store
}
function run(array $args): void {
    $values = ["payload" => "clean"];
    write_source($values); // DFB-WITNESS: issue303-invoke
    dfb_sink($values["payload"]); // DFB-WITNESS: issue303-read
}
run(array_slice($argv, 1));
