#!/bin/sh
set -eu
cd /Users/dave/.codex/worktrees/9f01/dataflowbench
v092_supervision=reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/supervision-04
(set -C; : > "$v092_supervision/launch-once.marker")
nohup /usr/bin/caffeinate -dimsu /usr/bin/python3 -B scripts/bifrost_v0144_benchmark.py execute --contract reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/contract-02.json --mode one --group bifrost-smoke > "$v092_supervision/controller.stdout" 2> "$v092_supervision/controller.stderr" < /dev/null &
v092_benchmark_launcher_pid=$!
printf '%s\n' "$v092_benchmark_launcher_pid" > "$v092_supervision/launcher.pid"
