<?php
function dfb_source(): string { // DFB-SOURCE: exception-persistence-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: exception-persistence-sink

final class FlowException extends \RuntimeException
{
}

class FlowBox
{
    public string $value;

    public function __construct(string $value)
    {
        $this->value = $value;
    }
}

function store_and_throw(FlowBox $box, string $value): void
{
    $box->value = $value; // DFB-WITNESS: exception-persistence-store
    throw new FlowException("exceptional exit"); // DFB-WITNESS: exception-persistence-throw
}

function recover(FlowBox $box, string $value): string
{
    try {
        store_and_throw($box, $value);
        return "unreachable";
    } catch (FlowException $_ignored) {
        return $box->value; // DFB-WITNESS: exception-persistence-recovery
    }
}

function run(): void
{
    dfb_sink(recover(new FlowBox("seed"), dfb_source()));
}
