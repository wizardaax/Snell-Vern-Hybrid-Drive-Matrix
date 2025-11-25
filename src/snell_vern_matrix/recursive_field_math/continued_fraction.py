from .lucas import L


def lucas_ratio_cfrac(n: int):
    """Return (numerator, denominator) for L_{n+1}/L_n and its continued-fraction pattern meta.
    Pattern: [1; 1,1,...,1, 3] with (n-2) ones (for n>=2).
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    num, den = L(n + 1), L(n)
    ones = max(0, n - 2)
    return (num, den, {"head": 1, "ones": ones, "tail": 3})
