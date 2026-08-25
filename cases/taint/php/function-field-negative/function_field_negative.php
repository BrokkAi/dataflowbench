<?php
class Holder
{
    public ?\Closure $fn = null;
}

function dfb_source(): string { // DFB-SOURCE: function-field-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: function-field-sink

function dispatch(Holder $holder, string $value): void
{
    ($holder->fn)($value);
}

function run(): void {
    $holder = new Holder();
    $holder->fn = function (string $value): void { // DFB-WITNESS: function-field-store
        dfb_sink($value);
    };
    $other = new Holder();
    $other->fn = function (string $value): void {
        dfb_sink("clean");
    };
    dispatch($other, dfb_source());
}
