"""Arquivo de testes GERADO automaticamente pelo experimento.

Variação: failing-2
extra_tests=10 include_slow=False slow_seconds=0.0 include_failing=True
"""

from calc import add, mul


def test_generated_0():
    assert add(0, 0) == 0
    assert mul(0, 1) == 0

def test_generated_1():
    assert add(1, 1) == 2
    assert mul(1, 1) == 1

def test_generated_2():
    assert add(2, 2) == 4
    assert mul(2, 1) == 2

def test_generated_3():
    assert add(3, 3) == 6
    assert mul(3, 1) == 3

def test_generated_4():
    assert add(4, 4) == 8
    assert mul(4, 1) == 4

def test_generated_5():
    assert add(5, 5) == 10
    assert mul(5, 1) == 5

def test_generated_6():
    assert add(6, 6) == 12
    assert mul(6, 1) == 6

def test_generated_7():
    assert add(7, 7) == 14
    assert mul(7, 1) == 7

def test_generated_8():
    assert add(8, 8) == 16
    assert mul(8, 1) == 8

def test_generated_9():
    assert add(9, 9) == 18
    assert mul(9, 1) == 9

def test_generated_failing():
    # Falha proposital para a variação 'failing'.
    assert add(2, 2) == 5
