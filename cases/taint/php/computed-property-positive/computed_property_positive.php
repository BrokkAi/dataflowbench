<?php
class Holder
{
    public string $alpha = "clean";
    public string $beta = "clean";
}

function dfb_source(): string { // DFB-SOURCE: computed-property-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: computed-property-sink

function run(): void {
    $holder = new Holder();
    $key = "alpha";
    $holder->{$key} = dfb_source(); // DFB-WITNESS: computed-property-store
    dfb_sink($holder->{$key});
}
