#!/usr/bin/env python3
"""Gera tests/test_generated.py de acordo com experiment/flags.env.

Permite variar de forma controlada:
  * EXTRA_TESTS    -> aumenta artificialmente a quantidade de testes
  * INCLUDE_SLOW   -> adiciona um teste lento (time.sleep)
  * SLOW_SECONDS   -> duração do teste lento
  * INCLUDE_FAILING-> adiciona um teste que falha de propósito

É chamado pelo driver do experimento antes de cada commit, mas também pode
ser executado manualmente para reproduzir uma variação.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ROOT / "experiment" / "flags.env"
OUT = ROOT / "tests" / "test_generated.py"


def read_flags() -> dict[str, str]:
    flags: dict[str, str] = {}
    if FLAGS.exists():
        for line in FLAGS.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            flags[key.strip()] = value.strip()
    return flags


def as_bool(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def main() -> None:
    flags = read_flags()
    extra = int(flags.get("EXTRA_TESTS", os.environ.get("EXTRA_TESTS", "0")) or 0)
    include_slow = as_bool(flags.get("INCLUDE_SLOW", os.environ.get("INCLUDE_SLOW")))
    slow_seconds = float(flags.get("SLOW_SECONDS", os.environ.get("SLOW_SECONDS", "0")) or 0)
    include_failing = as_bool(flags.get("INCLUDE_FAILING", os.environ.get("INCLUDE_FAILING")))
    variation = flags.get("VARIATION", "baseline")

    # Determina exatamente quais nomes serão usados (evita imports não usados no lint).
    calc_names: set[str] = set()
    if extra > 0:
        calc_names.update({"add", "mul"})
    if include_slow and slow_seconds > 0:
        calc_names.add("is_prime")
    if include_failing or not calc_names:
        calc_names.add("add")

    header: list[str] = [
        '"""Arquivo de testes GERADO automaticamente pelo experimento.',
        "",
        f"Variação: {variation}",
        f"extra_tests={extra} include_slow={include_slow} "
        f"slow_seconds={slow_seconds} include_failing={include_failing}",
        '"""',
        "",
    ]
    if include_slow and slow_seconds > 0:
        header.append("import time")
        header.append("")
    header.append("from calc import " + ", ".join(sorted(calc_names)))
    header.append("")
    header.append("")
    lines: list[str] = header

    # Testes "extras" baratos para inflar artificialmente a contagem de testes.
    for i in range(extra):
        lines.append(f"def test_generated_{i}():")
        lines.append(f"    assert add({i}, {i}) == {2 * i}")
        lines.append(f"    assert mul({i}, 1) == {i}")
        lines.append("")

    if include_slow and slow_seconds > 0:
        lines.append("def test_generated_slow():")
        lines.append(f"    time.sleep({slow_seconds})")
        lines.append("    assert is_prime(7) is True")
        lines.append("")

    if include_failing:
        lines.append("def test_generated_failing():")
        lines.append("    # Falha proposital para a variação 'failing'.")
        lines.append("    assert add(2, 2) == 5")
        lines.append("")

    if extra == 0 and not include_slow and not include_failing:
        lines.append("def test_generated_placeholder():")
        lines.append("    assert add(1, 1) == 2")
        lines.append("")

    OUT.write_text("\n".join(lines))
    print(f"Gerado {OUT} (variação={variation}, extra={extra}, "
          f"slow={include_slow}/{slow_seconds}s, failing={include_failing})")


if __name__ == "__main__":
    main()
