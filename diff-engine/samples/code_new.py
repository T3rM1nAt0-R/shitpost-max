def fibonacci(n):
    """Compute the nth Fibonacci number (iterative)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def factorial(n):
    """Compute n! using recursion."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def gcd(a, b):
    """Compute the greatest common divisor."""
    while b:
        a, b = b, a % b
    return a
