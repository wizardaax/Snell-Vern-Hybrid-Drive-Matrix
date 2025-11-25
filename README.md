# Snell-Vern Hybrid Drive Matrix

A unified Python engine that combines multiple mathematical and symbolic processing components for recursive field computations, phase-state tracking, and sequence analysis.

## Overview

The Snell-Vern Drive Matrix integrates three powerful components:

1. **Glyph Phase Engine** - Processes symbolic input and adjusts operational phase based on dynamic delta values
2. **Recursive Field Math** - Lucas 4-7-11 sequences, Fibonacci, ratio analysis, and generating functions
3. **Recursive Field** - Phyllotaxis pattern mathematics based on the golden angle

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

## Mathematical Background

### Golden Ratio (φ)
```
φ = (1 + √5) / 2 ≈ 1.618033988749895
```

### Golden Angle
```
θ = 180° × (3 - √5) ≈ 137.508°
```

### Lucas Numbers
```
L(0) = 2, L(1) = 1
L(n) = L(n-1) + L(n-2)

Sequence: 2, 1, 3, 4, 7, 11, 18, 29, 47, ...
```

### Lucas 4-7-11 Signature
The triplet (L3, L4, L5) = (4, 7, 11) has special properties:
- Egyptian fraction: 1/4 + 1/7 + 1/11 = 149/308
- Frobenius number: 4×7 - 4 - 7 = 17
- Additive chain: 4 + 7 = 11

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=snell_vern_matrix

# Run specific test file
pytest tests/test_drive_matrix.py
```

## Project Structure

```
Snell-Vern-Hybrid-Drive-Matrix/
├── src/
│   └── snell_vern_matrix/
│       ├── __init__.py              # Main package exports
│       ├── drive_matrix.py          # Unified DriveMatrix engine
│       ├── glyph_phase_engine/      # Phase-state tracking
│       │   ├── __init__.py
│       │   └── engine.py
│       ├── recursive_field_math/    # Lucas/Fibonacci math
│       │   ├── __init__.py
│       │   ├── constants.py
│       │   ├── fibonacci.py
│       │   ├── lucas.py
│       │   ├── field.py
│       │   ├── ratios.py
│       │   ├── continued_fraction.py
│       │   ├── egyptian_fraction.py
│       │   ├── generating_functions.py
│       │   └── signatures.py
│       └── recursive_field/         # Phyllotaxis patterns
│           ├── __init__.py
│           └── core.py
├── tests/
│   ├── test_drive_matrix.py
│   ├── test_glyph_phase_engine.py
│   ├── test_recursive_field.py
│   └── test_recursive_field_math.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Integrated Repositories

This project merges functionality from:

- [glyph_phase_engine](https://github.com/wizardaax/glyph_phase_engine) - Symbolic input and phase processing
- [recursive-field-math-pro](https://github.com/wizardaax/recursive-field-math-pro) - Lucas 4-7-11, CLI, and tests
- [recursive-field-math](https://github.com/wizardaax/recursive-field-math) - Phyllotaxis pattern formulas

## License

MIT License
