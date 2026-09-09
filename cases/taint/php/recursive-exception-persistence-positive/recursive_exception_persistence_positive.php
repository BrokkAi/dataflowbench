<?php
final class RecursiveSignal extends \RuntimeException
{
}

final class FlowBox
{
    public int $value;

    public function __construct(int $value)
    {
        $this->value = $value;
    }
}

function dfb_source(): int { // DFB-SOURCE: recursive-exception-persistence-input
    return 7;
}

function dfb_sink(int $value): void {} // DFB-SINK: recursive-exception-persistence-sink

function walk(FlowBox $box, int $value, int $depth): void
{
    if ($depth === 0) {
        $box->value = $value; // DFB-WITNESS: recursive-exception-persistence-base
        throw new RecursiveSignal('recursive exit'); // DFB-WITNESS: recursive-exception-persistence-throw
    }
    walk($box, $value, $depth - 1); // DFB-WITNESS: recursive-exception-persistence-transfer
}

function run(): void
{
    $box = new FlowBox(0);
    try {
        walk($box, dfb_source(), 3);
    } catch (RecursiveSignal $_caught) { // DFB-WITNESS: recursive-exception-persistence-catch
        dfb_sink($box->value + 1); // DFB-WITNESS: recursive-exception-persistence-compose
    }
}
