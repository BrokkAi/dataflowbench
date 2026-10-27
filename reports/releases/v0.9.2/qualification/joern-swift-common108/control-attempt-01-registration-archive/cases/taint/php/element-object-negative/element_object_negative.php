<?php
class Item
{
    public string $value = "clean";
}

function dfb_source(): string { // DFB-SOURCE: element-object-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: element-object-sink

function run(): void {
    $items = [new Item(), new Item()];
    $items[0]->value = dfb_source(); // DFB-WITNESS: element-object-store
    $items[1]->value = "clean";
    dfb_sink($items[1]->value);
}
