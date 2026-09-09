<?php
function dfb_source(): int { // DFB-SOURCE: recursive-payload-transform-input
    return 7;
}

function dfb_sink(int $value): void {} // DFB-SINK: recursive-payload-transform-sink

function walk(int $value, int $depth): int
{
    if ($depth === 0) {
        return $value; // DFB-WITNESS: recursive-payload-transform-base
    }
    $next = $value + 1;
    $recursive = walk($next, $depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
    return $recursive + 1; // DFB-WITNESS: recursive-payload-transform-compose
}

function run(): void
{
    dfb_sink(walk(dfb_source(), 3));
}
