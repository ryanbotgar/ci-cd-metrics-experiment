"""Arquivo de testes GERADO automaticamente pelo experimento.

Variação: slow-test-5s
extra_tests=0 include_slow=True slow_seconds=5.0 include_failing=False
"""

import time

from calc import is_prime


def test_generated_slow():
    time.sleep(5.0)
    assert is_prime(7) is True
