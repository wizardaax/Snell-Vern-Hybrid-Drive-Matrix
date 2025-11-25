def egypt_4_7_11():
    """Return exact rational sum for 1/4 + 1/7 + 1/11 = 149/308."""
    from fractions import Fraction

    s = Fraction(1, 4) + Fraction(1, 7) + Fraction(1, 11)
    return s.numerator, s.denominator
