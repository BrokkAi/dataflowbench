<?php
class Registry
{
    public array $hooks = [];

    public function register(\Closure $hook): void
    {
        $this->hooks[] = $hook;
    }

    public function fire(string $value): void // DFB-WITNESS: callback-registration-fire
    {
        foreach ($this->hooks as $hook) {
            $hook($value);
        }
    }
}

function dfb_source(): string { // DFB-SOURCE: callback-registration-input
    return "tainted";
}

function dfb_sink(string $value): void {} // DFB-SINK: callback-registration-sink

function run(): void {
    $registry = new Registry();
    $registry->register(function (string $value): void {
        dfb_sink("clean");
    });
    $registry->fire(dfb_source());
}
