<?php
function dfb_source(): string { // DFB-SOURCE: array-element-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: array-element-sink

function run(): void {
    $values = ["tainted" => "clean", "clean" => "clean"];
    $values["tainted"] = dfb_source(); // DFB-WITNESS: array-element-store
    $values["clean"] = "clean";
    dfb_sink($values["tainted"]);
}
