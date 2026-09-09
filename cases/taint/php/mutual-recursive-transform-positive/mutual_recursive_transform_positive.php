<?php
function dfb_source(): int { // DFB-SOURCE: mutual-recursive-transform-input
    return 7;
}

function dfb_sink(int $value): void {} // DFB-SINK: mutual-recursive-transform-sink

function walkA(int $value, int $depth): int
{
    if ($depth === 0) {
        return $value;
    }
    $next = $value + 1;
    $recursive = walkB($next, $depth - 1); // DFB-WITNESS: mutual-recursive-transform-a-transfer
    return $recursive + 1; // DFB-WITNESS: mutual-recursive-transform-a-compose
}

function walkB(int $value, int $depth): int
{
    if ($depth === 0) {
        return $value; // DFB-WITNESS: mutual-recursive-transform-b-base
    }
    $next = $value + 1;
    $recursive = walkA($next, $depth - 1); // DFB-WITNESS: mutual-recursive-transform-b-transfer
    return $recursive + 1; // DFB-WITNESS: mutual-recursive-transform-b-compose
}

function run(): void
{
    dfb_sink(walkA(dfb_source(), 3));
}
