<?php
interface Handler
{
    public function handle(string $value): void;
}

function dfb_source(): string { // DFB-SOURCE: anonymous-implementation-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: anonymous-implementation-sink

function run(): void {
    $leak = new class implements Handler { // DFB-WITNESS: anonymous-implementation-bind
        public function handle(string $value): void
        {
            dfb_sink($value);
        }
    };
    $drop = new class implements Handler {
        public function handle(string $value): void
        {
            dfb_sink("clean");
        }
    };
    $leak->handle(dfb_source());
}
