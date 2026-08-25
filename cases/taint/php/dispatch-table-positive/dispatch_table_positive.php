<?php
function dfb_source(): string { // DFB-SOURCE: dispatch-table-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: dispatch-table-sink

function run(): void {
    $table = [ // DFB-WITNESS: dispatch-table-build
        "leak" => function (string $value): void {
            dfb_sink($value);
        },
        "drop" => function (string $value): void {
            dfb_sink("clean");
        },
    ];
    $key = "leak";
    $table[$key](dfb_source());
}
