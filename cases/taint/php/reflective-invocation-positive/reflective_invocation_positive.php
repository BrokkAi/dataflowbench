<?php
class Target
{
    public function leak(string $value): void
    {
        dfb_sink($value);
    }

    public function drop(string $value): void
    {
        dfb_sink("clean");
    }
}

function dfb_source(): string { // DFB-SOURCE: reflective-invocation-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: reflective-invocation-sink

function run(): void {
    $target = new Target();
    $name = "leak";
    $target->$name(dfb_source()); // DFB-WITNESS: reflective-invocation-resolve
}
