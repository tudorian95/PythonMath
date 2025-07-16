def calc_pow(a: int, b: int) -> int:
    return a ** b

def calc_fib(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n+1):
        a, b = b, a + b
    return b

def calc_fact(n: int) -> int:
    if n < 0:
        raise ValueError("Negative factorial not defined")
    res = 1
    for i in range(2, n+1):
        res *= i
    return res