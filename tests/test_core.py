"""Conjunto de testes base da biblioteca calc."""

import pytest

from calc import add, div, factorial, fib, is_prime, mul, power, sub


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_sub():
    assert sub(5, 2) == 3
    assert sub(0, 4) == -4


def test_mul():
    assert mul(3, 4) == 12
    assert mul(-2, 5) == -10


def test_div():
    assert div(10, 2) == 5
    assert div(9, 3) == 3


def test_div_by_zero():
    with pytest.raises(ZeroDivisionError):
        div(1, 0)


def test_power():
    assert power(2, 10) == 1024
    assert power(5, 0) == 1


def test_factorial():
    assert factorial(0) == 1
    assert factorial(5) == 120


def test_factorial_negative():
    with pytest.raises(ValueError):
        factorial(-1)


@pytest.mark.parametrize("n,expected", [(1, False), (2, True), (17, True), (18, False)])
def test_is_prime(n, expected):
    assert is_prime(n) is expected


def test_fib():
    assert fib(0) == 0
    assert fib(10) == 55
