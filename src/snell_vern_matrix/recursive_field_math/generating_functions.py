def GF_F(x: float) -> float:
    """Ordinary generating function for Fibonacci: sum_{n>=0} F_n x^n = x / (1 - x - x^2)."""
    denom = 1 - x - x * x
    if denom == 0:
        raise ZeroDivisionError("Singularity at 1 - x - x^2 = 0")
    return x / denom


def GF_L(x: float) -> float:
    """Ordinary generating function for Lucas: sum_{n>=0} L_n x^n = (2 - x) / (1 - x - x^2)."""
    denom = 1 - x - x * x
    if denom == 0:
        raise ZeroDivisionError("Singularity at 1 - x - x^2 = 0")
    return (2 - x) / denom
