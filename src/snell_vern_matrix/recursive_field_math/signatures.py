"""
Lucas 4-7-11 signature analysis and Frobenius number computation.

The Lucas 4-7-11 Signature:
The triplet (L₃, L₄, L₅) = (4, 7, 11) has special mathematical properties
that make it particularly useful in number theory and cryptographic applications.

Properties:

1. **Additive Chain**: L₃ + L₄ = 4 + 7 = 11 = L₅
   This creates a natural hierarchical structure for field subdivision.

2. **Frobenius Number**: For coprime integers a and b, the Frobenius number
   F(a,b) = ab - a - b is the largest integer that CANNOT be represented as
   a non-negative integer linear combination of a and b.

   For (4, 7): F(4,7) = 4×7 - 4 - 7 = 28 - 11 = 17

   This means 17 is the largest number that cannot be written as 4x + 7y
   for non-negative integers x, y.

   Verification:
   - 17 cannot be written as 4x + 7y (x,y ≥ 0)
   - 18 = 4×0 + 7×2 + 4 = 4 + 7×2 (can be represented, but also 18 = 4×4 + 7×0 + 2... actually 18 = 7×2 + 4×1)
   - All integers ≥ 18 can be represented

3. **Egyptian Fraction**: 1/4 + 1/7 + 1/11 = 149/308
   A unit fraction sum with prime numerator (149 is prime).

4. **Pair Products**:
   - L₃ × L₄ = 4 × 7 = 28
   - L₃ × L₅ = 4 × 11 = 44
   - L₄ × L₅ = 7 × 11 = 77
   - Sum: 28 + 44 + 77 = 149 (same as Egyptian fraction numerator!)

5. **Triple Product**: L₃ × L₄ × L₅ = 4 × 7 × 11 = 308 (Egyptian fraction denominator)

Applications in Cryptography:
- **Entropy Gaps**: The Frobenius number creates natural gaps in representable
  integers, useful for entropy generation
- **Key Spacing**: The pair sums provide non-trivial spacing for key schedules
- **Hash Functions**: The 149/308 ratio provides near-irrational mixing
- **Pseudorandom Sequences**: Additive chain creates hierarchical structure

The Coin Problem:
The Frobenius number solves the "coin problem": given coin denominations,
what's the largest amount that cannot be made? For 4 and 7 cent coins,
you cannot make exactly 17 cents, but you can make any amount ≥ 18 cents.
"""

from .lucas import L


def signature_summary():
    """
    Compute comprehensive analysis of the Lucas 4-7-11 signature.

    Returns a dictionary containing:
    - L3, L4, L5: The Lucas numbers 4, 7, 11
    - product: L3 × L4 × L5 = 308
    - pair_sum: (L3×L4) + (L3×L5) + (L4×L5) = 149
    - frobenius_4_7: The Frobenius number F(4,7) = 17
    - additive_chain: Boolean indicating if L3 + L4 = L5 (True)

    Returns:
        Dictionary with signature properties and relationships

    Examples:
        >>> sig = signature_summary()
        >>> sig['L3'], sig['L4'], sig['L5']
        (4, 7, 11)
        >>> sig['product']
        308
        >>> sig['pair_sum']
        149
        >>> sig['frobenius_4_7']
        17
        >>> sig['additive_chain']
        True

    Mathematical Note:
        The fact that pair_sum = 149 and product = 308 is not coincidental:

        For the Egyptian fraction 1/4 + 1/7 + 1/11:
            Common denominator = 4 × 7 × 11 = 308
            1/4 = 77/308  (multiply by 77 = 7×11)
            1/7 = 44/308  (multiply by 44 = 4×11)
            1/11 = 28/308 (multiply by 28 = 4×7)

        The numerators are exactly the pairwise products, and their sum is:
            77 + 44 + 28 = 149 = pair_sum

        This creates a beautiful connection between:
        - Lucas sequence properties
        - Egyptian fractions
        - Pairwise products
        - The Frobenius number

        All arising from the single triplet (4, 7, 11)!
    """
    l3, l4, l5 = L(3), L(4), L(5)
    # Triple product: used as denominator in Egyptian fraction
    prod = l3 * l4 * l5
    # Sum of pairwise products: equals numerator of Egyptian fraction
    pair_sum = (l3 * l4) + (l3 * l5) + (l4 * l5)
    return {
        "L3": l3,
        "L4": l4,
        "L5": l5,
        "product": prod,  # 308
        "pair_sum": pair_sum,  # 149
        "frobenius_4_7": 4 * 7 - 4 - 7,  # 17
        "additive_chain": (4 + 7 == 11),  # True
    }
