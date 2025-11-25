# Snell-Vern Hybrid Drive Matrix

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

A unified Python engine that combines multiple mathematical and symbolic processing components for recursive field computations, phase-state tracking, and sequence analysis.

## 🌟 Showcase - Key Innovations

The Snell-Vern Hybrid Drive Matrix represents a novel approach to mathematical computation that unifies several advanced concepts:

- **🔮 Symbolic Phase Processing**: Dynamic phase-state tracking that adapts to symbolic input patterns, enabling self-adjusting computational flows
- **📐 Golden Ratio Field Theory**: Leverages the golden angle (φ ≈ 137.508°) for phyllotaxis pattern generation with applications in natural growth modeling
- **🔢 Lucas 4-7-11 Signature**: Exploits special properties of the Lucas triplet (L₃=4, L₄=7, L₅=11) including Egyptian fractions and Frobenius numbers
- **♾️ Recursive Convergence Analysis**: Tracks ratio convergence to PHI with mathematically rigorous error bounds
- **🎯 Ternary Logic Foundations**: Field structures supporting three-state logic for symbolic computation
- **🔐 Cryptographic-Grade Entropy**: Mathematical primitives designed for use in entropy generation and cryptographic applications

## 🎯 Motivation

This project emerged from the intersection of number theory, symbolic mathematics, and natural pattern analysis. By unifying Lucas sequences, Fibonacci mathematics, and phyllotaxis patterns into a single computational framework, we enable:

- **Research Applications**: Mathematical exploration of recursive sequences and their convergence properties
- **Natural Pattern Modeling**: Simulation of plant growth patterns and spiral phyllotaxis
- **Cryptographic Primitives**: Foundation for entropy-based cryptographic operations using golden ratio properties
- **Educational Tools**: Interactive demonstration of advanced mathematical concepts
- **Symbolic Processing**: Framework for building logic engines with phase-state awareness

## Overview

The Snell-Vern Drive Matrix integrates three powerful components:

1. **Glyph Phase Engine** - Processes symbolic input and adjusts operational phase based on dynamic delta values, enabling adaptive computation
2. **Recursive Field Math** - Lucas 4-7-11 sequences, Fibonacci numbers, ratio analysis, generating functions, and continued fractions
3. **Recursive Field** - Phyllotaxis pattern mathematics based on the golden angle, modeling natural spiral growth

## Installation

```bash
pip install -e .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from snell_vern_matrix import DriveMatrix, MatrixState

# Create the unified engine
matrix = DriveMatrix()

# Process symbolic input
state = matrix.process_input("compute field")
print(f"Matrix state: {state}")

# Compute phyllotaxis field positions
field = matrix.compute_field(1, 10)
for i, (x, y) in enumerate(field, 1):
    print(f"Position {i}: ({x:.3f}, {y:.3f})")

# Compute Fibonacci and Lucas sequences
sequences = matrix.compute_sequences(15)
print(f"Fibonacci: {list(sequences['fibonacci'].values())}")
print(f"Lucas: {list(sequences['lucas'].values())}")

# Analyze Lucas ratios convergence to PHI
analysis = matrix.analyze_lucas_ratios(10)
print(f"PHI: {analysis['phi']}")
print(f"Egyptian fraction 1/4 + 1/7 + 1/11 = {analysis['egyptian_fraction']}")

# Get golden angle field analysis
golden = matrix.get_golden_field_analysis()
print(f"Golden Angle: {golden['golden_angle_degrees']:.3f}°")
```

## Components

### GlyphPhaseEngine

Phase-state tracking engine for symbolic input processing:

```python
from snell_vern_matrix import GlyphPhaseEngine, PhaseState

engine = GlyphPhaseEngine()
state = engine.process_symbolic_input("analyze pattern")
print(f"Phase: {state}")  # PhaseState.STABILIZED

# Adjust phase with delta values
engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
new_state = engine.adjust_phase_delta(0.05)
print(f"After delta: {new_state}")  # PhaseState.STABILIZED
```

### Recursive Field Math (Lucas 4-7-11)

Mathematical functions for Lucas and Fibonacci sequences:

```python
from snell_vern_matrix import F, L, PHI, ratio, egypt_4_7_11, signature_summary

# Fibonacci and Lucas numbers
print(F(10))  # 55
print(L(5))   # 11 (Lucas numbers: 2, 1, 3, 4, 7, 11, ...)

# Golden ratio
print(PHI)    # 1.618...

# Lucas ratio convergence
print(ratio(5))  # L(6)/L(5) approaches PHI

# Egyptian fraction: 1/4 + 1/7 + 1/11 = 149/308
num, den = egypt_4_7_11()
print(f"{num}/{den}")

# Signature summary with L3=4, L4=7, L5=11
sig = signature_summary()
print(sig)
```

### Recursive Field (Phyllotaxis)

Golden angle based field calculations:

```python
from snell_vern_matrix import golden_angle, radius, angle, position

# Golden angle (~137.508°)
ga = golden_angle()
print(f"Golden angle: {ga:.3f}°")

# Radius at index n: r_n = a * sqrt(n)
r = radius(5)       # 3 * sqrt(5) ≈ 6.708
r = radius(5, a=2)  # 2 * sqrt(5) ≈ 4.472

# Angle at index n: θ_n = n * golden_angle (mod 360)
theta = angle(5)

# Cartesian position
x, y = position(10)
```

## 📚 Advanced Mathematical Background

### The Snell-Vern Framework

The Snell-Vern formalism extends classical recursive sequence theory by introducing **phase-coherent field structures** that combine:

1. **Algebraic Number Theory**: Leveraging the golden ratio φ and its conjugate ψ
2. **Symbolic Logic Processing**: Three-state (ternary) logic for glyph representation
3. **Dynamical Systems**: Phase-state tracking with delta-based convergence
4. **Combinatorial Number Theory**: Egyptian fractions and Frobenius numbers

### Golden Ratio (φ) and Its Conjugate

The golden ratio φ is an algebraic number satisfying φ² = φ + 1:

```
φ = (1 + √5) / 2 ≈ 1.618033988749895 (positive root)
ψ = (1 - √5) / 2 ≈ -0.618033988749895 (conjugate, negative root)
```

**Properties**:
- φ + ψ = 1
- φ × ψ = -1
- φⁿ and ψⁿ govern Fibonacci and Lucas sequences via Binet's formula

### Golden Angle in Phyllotaxis

The golden angle arises from dividing the circle in golden ratio proportion:

```
θ = 360° × (1 - 1/φ) = 360° × (2 - φ) = 180° × (3 - √5) ≈ 137.507764°
```

This angle appears in natural phyllotaxis (leaf arrangement) because it provides optimal packing without overlapping spirals. Each subsequent seed/leaf rotates by θ from the previous, creating Fibonacci spiral patterns.

### Lucas Numbers and Fibonacci Sequences

**Fibonacci Sequence** F(n):
```
F(0) = 0, F(1) = 1
F(n) = F(n-1) + F(n-2)
Sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

Binet Formula: F(n) = (φⁿ - ψⁿ) / √5
```

**Lucas Sequence** L(n):
```
L(0) = 2, L(1) = 1
L(n) = L(n-1) + L(n-2)
Sequence: 2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, ...

Closed Form: L(n) = φⁿ + ψⁿ
```

**Convergence Property**:
```
lim(n→∞) F(n+1)/F(n) = φ
lim(n→∞) L(n+1)/L(n) = φ
```

With rigorous error bounds:
```
√5 / (Lₙ(Lₙ + |ψ|ⁿ)) ≤ |L(n+1)/L(n) - φ| ≤ √5 / (Lₙ(Lₙ - |ψ|ⁿ))
```

### The Lucas 4-7-11 Signature

The triplet (L₃, L₄, L₅) = (4, 7, 11) exhibits remarkable mathematical properties exploited in this framework:

**Egyptian Fraction Decomposition**:
```
1/4 + 1/7 + 1/11 = (77 + 44 + 28) / 308 = 149/308
```

**Frobenius Number** (coin problem):
```
F(4,7) = 4×7 - 4 - 7 = 17
```
The largest number that cannot be represented as a non-negative integer linear combination of 4 and 7.

**Additive Chain Property**:
```
L₃ + L₄ = 4 + 7 = 11 = L₅
```

**Applications in the Matrix**:
- **Entropy Generation**: The 149/308 fraction provides a near-irrational approximation useful for pseudorandom sequences
- **Cryptographic Spacing**: Frobenius gaps create natural entropy pockets
- **Field Indexing**: The additive chain enables hierarchical field subdivision

### Field Structures and Ternary Logic

The **Field** component models positions in a phyllotaxis-style arrangement:

```
Position n in polar coordinates:
r(n) = a√n          (radius grows as square root)
θ(n) = n × θ_golden (mod 360°)  (angle increments by golden angle)

Cartesian conversion:
x(n) = r(n) × cos(θ(n))
y(n) = r(n) × sin(θ(n))
```

**Ternary Logic Foundation**:
The Glyph Phase Engine operates on three-state logic:
- **State 0**: Initial/Idle (未)
- **State 1**: Processing/Active (動)
- **State 2**: Stabilized/Complete (定)

This ternary foundation enables:
- **Balanced Ternary Arithmetic**: {-1, 0, 1} representation
- **Three-Valued Logic**: Beyond classical binary true/false
- **Symbolic Glyph Encoding**: Mapping complex symbols to ternary states

### Glyph Symbolic Processing

Glyphs represent symbolic mathematical objects processed through phase transitions:

```
Symbolic Input → Processing → Delta Adjustment → Stabilization
     |              |               |                  |
  (Initial)    (Computing)   (Refinement)        (Converged)
```

**Phase Delta Mechanism**:
- Small delta (|Δ| < 0.1): Converges to stabilization
- Large delta (|Δ| > 1.0): Triggers error state
- Moderate delta: Continues adjustment cycles

This creates a **self-regulating computational flow** where the system adapts based on input characteristics and convergence rates.

### Entropy and Cryptographic Applications

**Sources of Entropy**:
1. **Golden Ratio Irrationality**: φ's continued fraction expansion [1;1,1,1,1,...] provides unbounded randomness
2. **Lucas Ratio Convergence**: Near-chaotic behavior in early terms before convergence
3. **Phyllotaxis Angular Spacing**: Near-uniform distribution avoiding resonances
4. **Egyptian Fraction Approximations**: Rational approximations to irrational targets

**Cryptographic Hygiene**:
- All arithmetic uses exact integer operations (Fibonacci/Lucas via Binet)
- Floating-point used only for geometric visualization
- No hardcoded secrets or keys
- Mathematical constants derived from first principles

### Generating Functions and Analytic Properties

**Fibonacci Generating Function**:
```
G_F(x) = Σ(n≥0) F(n)xⁿ = x / (1 - x - x²)
```

**Lucas Generating Function**:
```
G_L(x) = Σ(n≥0) L(n)xⁿ = (2 - x) / (1 - x - x²)
```

These rational generating functions encode the entire sequence in closed form and enable:
- **Power Series Expansion**: Extracting coefficients via Taylor series
- **Asymptotic Analysis**: Singularity at roots of 1 - x - x² = 0
- **Combinatorial Identities**: Proving identities via algebraic manipulation

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=snell_vern_matrix --cov-report=html

# Run specific test file
pytest tests/test_drive_matrix.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_lucas"
```

**Current Test Coverage**: 38 tests covering all major components

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Build System**: Hatchling (PEP 517)
- **Testing**: pytest with coverage support
- **Linting**: Ruff (fast Python linter)
- **Type Checking**: mypy (static type analysis)
- **Dependencies**: Pure Python - zero runtime dependencies

**Design Philosophy**: Lightweight, mathematically rigorous, and dependency-free core library.

## 🤝 Contributing

Contributions are welcome! Areas of particular interest:

1. **Extended Sequences**: Tribonacci, Pell numbers, other recursive sequences
2. **Visualization Tools**: Plotting phyllotaxis patterns, convergence graphs
3. **Performance Optimization**: Memoization, matrix exponentiation for large n
4. **Additional Applications**: Cryptographic protocols, pattern recognition
5. **Documentation**: More examples, tutorials, mathematical proofs

Please ensure:
- All tests pass (`pytest`)
- Code is linted (`ruff check .`)
- Type hints are added (`mypy src/`)
- New features include tests and documentation

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Adam Snellman (wizardaax)

## 📧 Contact & Links

- **Author**: Adam Snellman (wizardaax)
- **Repository**: [github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)
- **Issues**: [Report bugs or request features](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/issues)
- **Discussions**: [Join the conversation](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/discussions)

## 🙏 Acknowledgments

This project merges and extends functionality from:

- [glyph_phase_engine](https://github.com/wizardaax/glyph_phase_engine) - Symbolic input and phase processing
- [recursive-field-math-pro](https://github.com/wizardaax/recursive-field-math-pro) - Lucas 4-7-11 sequences and mathematical foundations
- [recursive-field-math](https://github.com/wizardaax/recursive-field-math) - Phyllotaxis pattern formulas

Special thanks to the mathematical community for foundational work on:
- Golden ratio and Fibonacci sequences
- Phyllotaxis and botanical mathematics
- Continued fractions and Diophantine approximation

## 📚 Further Reading

**Mathematical References**:
- Knuth, D. E. "The Art of Computer Programming, Volume 1: Fundamental Algorithms" (Fibonacci and Lucas numbers)
- Vogel, H. "A better way to construct the sunflower head" (Phyllotaxis mathematics)
- Hardy, G. H. & Wright, E. M. "An Introduction to the Theory of Numbers" (Golden ratio properties)

**Related Projects**:
- [SymPy](https://www.sympy.org/) - Symbolic mathematics in Python
- [OEIS](https://oeis.org/) - Online Encyclopedia of Integer Sequences (Fibonacci: A000045, Lucas: A000032)

---

**Built with ❤️ and φ (the golden ratio)**
