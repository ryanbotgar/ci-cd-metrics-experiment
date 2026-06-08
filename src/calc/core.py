"""Funções matemáticas simples.

Este módulo é o "código de produção" do projeto. Os testes em ``tests/``
exercitam estas funções. O objetivo do repositório não é a biblioteca em si,
mas servir de alvo realista para instrumentar e medir um pipeline CI/CD.
"""

from __future__ import annotations


def add(a: float, b: float) -> float:
    return a + b


def sub(a: float, b: float) -> float:
    return a - b


def mul(a: float, b: float) -> float:
    return a * b


def div(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("divisão por zero")
    return a / b


def power(base: float, exp: int) -> float:
    return base ** exp


def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("fatorial não definido para negativos")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def fib(n: int) -> int:
    if n < 0:
        raise ValueError("fib não definido para negativos")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
