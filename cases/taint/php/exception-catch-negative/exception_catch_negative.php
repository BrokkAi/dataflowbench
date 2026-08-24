<?php
class FlowException extends \Exception
{
    public string $value = "clean";
}

function dfb_source(): string { // DFB-SOURCE: exception-catch-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: exception-catch-sink

function run(): void {
    try {
        $flow = new FlowException("flow");
        $ignored = dfb_source();
        $flow->value = "clean";
        throw $flow; // DFB-WITNESS: exception-catch-throw
    } catch (FlowException $caught) {
        dfb_sink($caught->value);
    }
}
