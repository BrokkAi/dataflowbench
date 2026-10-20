<?php
final class FlowBox
{
    public int $value;

    public function __construct(int $value)
    {
        $this->value = $value;
    }
}

function dfb_source(): int { // DFB-SOURCE: recursive-heap-unwind-input
    return 7;
}

function dfb_sink(int $value): void {} // DFB-SINK: recursive-heap-unwind-sink

function walk(FlowBox $box, int $value, int $depth): void
{
    if ($depth === 0) {
        $box->value = $value; // DFB-WITNESS: recursive-heap-unwind-base
        $box->value = 0; // DFB-KILL: recursive-heap-unwind-base-clean
        return;
    }
    walk($box, $value, $depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
    $box->value = $box->value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
}

function run(): void
{
    $box = new FlowBox(0);
    walk($box, dfb_source(), 3);
    dfb_sink($box->value);
}
