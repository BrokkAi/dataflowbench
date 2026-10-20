<?php
class Holder
{
    public string $tainted = "clean";
    public string $clean = "clean";
}

function dfb_source(): string { // DFB-SOURCE: same-object-field-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: same-object-field-sink

function run(): void {
    $holder = new Holder();
    $holder->tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
    $holder->clean = "clean";
    dfb_sink($holder->tainted);
}
