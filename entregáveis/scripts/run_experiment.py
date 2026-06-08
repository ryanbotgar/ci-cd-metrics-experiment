#!/usr/bin/env python3
"""Driver do experimento: aplica variações controladas e dispara execuções.

Para cada variação o script:
  1. reescreve experiment/flags.env;
  2. regenera tests/test_generated.py (scripts/gen_tests.py);
  3. ajusta o paralelismo dos jobs no workflow (needs: [lint] ou não);
  4. faz commit e push -> dispara o workflow CI no GitHub Actions.

Isso torna o experimento reproduzível: basta rodar este script no repositório.

Uso:
    python scripts/run_experiment.py            # todas as variações
    python scripts/run_experiment.py --sleep 25 # intervalo entre pushes
    python scripts/run_experiment.py --only baseline failing
"""

from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ROOT / "experiment" / "flags.env"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

# Cada variação: (nome, dict de flags, parallel?)
VARIATIONS: list[tuple[str, dict, bool]] = [
    # nome,                 flags,                                                        parallel
    ("baseline-1",          dict(USE_PIP_CACHE="true",  EXTRA_TESTS=0,   INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("baseline-2",          dict(USE_PIP_CACHE="true",  EXTRA_TESTS=0,   INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("failing-1",           dict(USE_PIP_CACHE="true",  EXTRA_TESTS=0,   INCLUDE_FAILING="true",  INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("failing-2",           dict(USE_PIP_CACHE="true",  EXTRA_TESTS=10,  INCLUDE_FAILING="true",  INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("more-tests-50",       dict(USE_PIP_CACHE="true",  EXTRA_TESTS=50,  INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("more-tests-200",      dict(USE_PIP_CACHE="true",  EXTRA_TESTS=200, INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("more-tests-500",      dict(USE_PIP_CACHE="true",  EXTRA_TESTS=500, INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("slow-test-5s",        dict(USE_PIP_CACHE="true",  EXTRA_TESTS=0,   INCLUDE_FAILING="false", INCLUDE_SLOW="true",  SLOW_SECONDS=5),  True),
    ("slow-test-15s",       dict(USE_PIP_CACHE="true",  EXTRA_TESTS=0,   INCLUDE_FAILING="false", INCLUDE_SLOW="true",  SLOW_SECONDS=15), True),
    ("no-cache-1",          dict(USE_PIP_CACHE="false", EXTRA_TESTS=0,   INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("no-cache-2",          dict(USE_PIP_CACHE="false", EXTRA_TESTS=50,  INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  True),
    ("sequential-1",        dict(USE_PIP_CACHE="true",  EXTRA_TESTS=0,   INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  False),
    ("sequential-2",        dict(USE_PIP_CACHE="true",  EXTRA_TESTS=50,  INCLUDE_FAILING="false", INCLUDE_SLOW="false", SLOW_SECONDS=0),  False),
    ("combo-slow-many-nocache", dict(USE_PIP_CACHE="false", EXTRA_TESTS=200, INCLUDE_FAILING="false", INCLUDE_SLOW="true", SLOW_SECONDS=10), True),
]


def write_flags(name: str, flags: dict) -> None:
    lines = [
        "# Flags da variação atual (gerado por run_experiment.py)",
        f"VARIATION={name}",
        f"USE_PIP_CACHE={flags['USE_PIP_CACHE']}",
        f"EXTRA_TESTS={flags['EXTRA_TESTS']}",
        f"INCLUDE_FAILING={flags['INCLUDE_FAILING']}",
        f"INCLUDE_SLOW={flags['INCLUDE_SLOW']}",
        f"SLOW_SECONDS={flags['SLOW_SECONDS']}",
        "",
    ]
    FLAGS.write_text("\n".join(lines))


def set_parallel(parallel: bool) -> None:
    text = WORKFLOW.read_text()
    seq_block = "    name: Test (pytest)\n    runs-on: ubuntu-latest\n    needs: [lint]\n"
    par_block = "    name: Test (pytest)\n    runs-on: ubuntu-latest\n"
    # normaliza para paralelo primeiro
    text = text.replace(seq_block, par_block)
    if not parallel:
        text = text.replace(par_block, seq_block)
    WORKFLOW.write_text(text)


def run(cmd: list[str]) -> None:
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def apply_and_push(name: str, flags: dict, parallel: bool) -> None:
    print(f"\n=== Variação: {name} (parallel={parallel}) ===")
    write_flags(name, flags)
    set_parallel(parallel)
    run(["python3", "scripts/gen_tests.py"])
    run(["git", "add", "-A"])
    msg = (
        f"exp({name}): cache={flags['USE_PIP_CACHE']} extra={flags['EXTRA_TESTS']} "
        f"fail={flags['INCLUDE_FAILING']} slow={flags['INCLUDE_SLOW']}/{flags['SLOW_SECONDS']}s "
        f"parallel={parallel}"
    )
    # --allow-empty caso nada mude entre repetições idênticas
    run(["git", "commit", "--allow-empty", "-m", msg])
    run(["git", "push"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sleep", type=int, default=20, help="segundos entre pushes")
    ap.add_argument("--only", nargs="*", help="rodar apenas variações com estes nomes")
    args = ap.parse_args()

    selected = VARIATIONS
    if args.only:
        selected = [v for v in VARIATIONS if v[0] in set(args.only)]

    for i, (name, flags, parallel) in enumerate(selected):
        apply_and_push(name, flags, parallel)
        if i < len(selected) - 1:
            print(f"  ... aguardando {args.sleep}s antes do próximo push")
            time.sleep(args.sleep)

    print("\nTodas as variações enviadas. Acompanhe em: gh run list")


if __name__ == "__main__":
    main()
