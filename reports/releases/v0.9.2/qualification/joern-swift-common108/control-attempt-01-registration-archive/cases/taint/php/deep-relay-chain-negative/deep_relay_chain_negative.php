<?php
function dfb_source(): string { // DFB-SOURCE: deep-relay-chain-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: deep-relay-chain-sink

function relay1(string $value): string { // DFB-WITNESS: deep-relay-chain-hop1
    return relay2($value);
}

function relay2(string $value): string { // DFB-WITNESS: deep-relay-chain-hop2
    return relay3($value);
}

function relay3(string $value): string { // DFB-WITNESS: deep-relay-chain-hop3
    return relay4($value);
}

function relay4(string $value): string { // DFB-WITNESS: deep-relay-chain-hop4
    return relay5($value);
}

function relay5(string $value): string { // DFB-WITNESS: deep-relay-chain-hop5
    return relay6($value);
}

function relay6(string $value): string { // DFB-WITNESS: deep-relay-chain-hop6
    return $value;
}

function run(): void {
    $tainted = dfb_source();
    dfb_sink(relay1("clean"));
}
