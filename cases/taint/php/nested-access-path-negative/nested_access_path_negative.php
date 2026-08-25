<?php
class Inner
{
    public string $value = "clean";
    public string $other = "clean";
}

class Middle
{
    public Inner $inner;

    public function __construct()
    {
        $this->inner = new Inner();
    }
}

class Outer
{
    public Middle $middle;

    public function __construct()
    {
        $this->middle = new Middle();
    }
}

function dfb_source(): string { // DFB-SOURCE: nested-access-path-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: nested-access-path-sink

function run(): void {
    $outer = new Outer();
    $outer->middle->inner->value = dfb_source(); // DFB-WITNESS: nested-access-path-store
    $outer->middle->inner->other = "clean";
    dfb_sink($outer->middle->inner->other);
}
