from .lucas import L


def signature_summary():
    l3, l4, l5 = L(3), L(4), L(5)
    prod = l3 * l4 * l5
    pair_sum = (l3 * l4) + (l3 * l5) + (l4 * l5)
    return {
        "L3": l3,
        "L4": l4,
        "L5": l5,
        "product": prod,
        "pair_sum": pair_sum,
        "frobenius_4_7": 4 * 7 - 4 - 7,
        "additive_chain": (4 + 7 == 11),
    }
