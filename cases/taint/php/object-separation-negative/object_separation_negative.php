<?php
class Holder
{
    public string $value = "clean";
}

function dfb_source(): string { // DFB-SOURCE: object-separation-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: object-separation-sink

function run(): void {
    $tainted = new Holder();
    $clean = new Holder();
    $tainted->value = dfb_source(); // DFB-WITNESS: object-separation-store
    $clean->value = "clean";
    dfb_sink($clean->value);
}
