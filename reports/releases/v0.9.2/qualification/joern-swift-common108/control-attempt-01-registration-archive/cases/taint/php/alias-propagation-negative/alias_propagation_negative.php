<?php
class Holder
{
    public string $value = "clean";
}

function dfb_source(): string { // DFB-SOURCE: alias-propagation-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: alias-propagation-sink

function run(): void {
    $original = new Holder();
    $alias = $original; // DFB-WITNESS: alias-propagation-alias
    $distinct = new Holder();
    $original->value = dfb_source(); // DFB-WITNESS: alias-propagation-store
    dfb_sink($distinct->value);
}
