<?php
function dfb_source(): int { // DFB-SOURCE: recursive-callback-transform-input
    return 7;
}

function dfb_sink(int $value): void {} // DFB-SINK: recursive-callback-transform-sink

function walk(int $value, int $depth, callable $step): int
{
    if ($depth === 0) {
        return $value; // DFB-WITNESS: recursive-callback-transform-base
    }
    return $step($value, $depth - 1); // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}

function step(int $value, int $depth): int
{
    $next = $value + 1; // DFB-WITNESS: recursive-callback-transform-step
    $recursive = walk($next, $depth, __FUNCTION__); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
    return $recursive + 1; // DFB-WITNESS: recursive-callback-transform-compose
}

function run(): void
{
    dfb_sink(walk(dfb_source(), 3, 'step'));
}
