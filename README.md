# Snell-Vern Hybrid Drive Matrix

[![Aeon Standards](https://img.shields.io/badge/aeon--standards-v1-blueviolet.svg)](https://github.com/wizardaax/aeon-standards)
[![Build](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Build/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/build.yml)
[![Tests](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Tests/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/test.yml)
[![Lint](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Lint/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/lint.yml)
[![Security](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Security/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/security.yml)
[![Aeon Python CI](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Aeon%20Python%20CI/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/aeon-python-ci.yml)
[![Aeon Security](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Aeon%20Security/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/aeon-security.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/snell-vern-matrix)](https://pypi.org/project/snell-vern-matrix/)
[![codecov](https://codecov.io/gh/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/branch/main/graph/badge.svg)](https://codecov.io/gh/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![OSSF Scorecard](https://api.scorecard.dev/projects/github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/badge)](https://scorecard.dev/viewer/?uri=github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)

A unified Python engine that combines mathematical and symbolic processing components for recursive field computations, phase-state tracking, and sequence analysis.

## Key Features

- **Symbolic Phase Processing**: Phase-state tracking that adapts to symbolic input patterns, enabling self-adjusting computational flows.
- **Golden Ratio Field Theory**: Uses the golden angle (φ ≈ 137.508°) for phyllotaxis pattern generation.
- **Lucas 4-7-11 Signature**: Exploits properties of the Lucas triplet (L₃=4, L₄=7, L₅=11) including Egyptian fractions and Frobenius numbers.
- **Recursive Convergence Analysis**: Tracks ratio convergence to PHI with rigorous error bounds.
- **Ternary Logic Foundations**: Field structures supporting three-state logic for symbolic computation.
- **Cryptographic-Grade Entropy**: Mathematical primitives for entropy generation and cryptographic applications.

## Motivation

Built at the intersection of number theory, symbolic mathematics, and natural pattern analysis. Unifies Lucas sequences, Fibonacci mathematics, and phyllotaxis patterns into a single framework for:

- **Research**: Mathematical exploration of recursive sequences and convergence properties.
- **Pattern Modelling**: Simulation of plant growth patterns and spiral phyllotaxis.
- **Cryptographic Primitives**: Foundation for entropy-based cryptographic operations using golden ratio properties.
- **Educational Tools**: Demonstration of advanced mathematical concepts.
- **Symbolic Processing**: Framework for logic engines with phase-state awareness.

## Overview

The Snell-Vern Drive Matrix integrates three components:

1. **Glyph Phase Engine** — Processes symbolic input and adjusts operational phase based on dynamic delta values.
2. **Recursive Field Math** — Lucas 4-7-11 sequences, Fibonacci numbers, ratio analysis, generating functions, and continued fractions.
3. **Recursive Field** — Phyllotaxis pattern mathematics based on the golden angle.

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from snell_vern_matrix import DriveMatrix, MatrixState

matrix = DriveMatrix()

state = matrix.process_input("compute field")
print(f"Matrix state: {state}")

field = matrix.compute_field(1, 10)
for i, (x, y) in enumerate(field, 1):
    print(f"Position {i}: ({x:.3f}, {y:.3f})")

sequences = matrix.compute_sequences(15)
print(f"Fibonacci: {list(sequences['fibonacci'].values())}")
print(f"Lucas: {list(sequences['lucas'].values())}")

analysis = matrix.analyze_lucas_ratios(10)
print(f"PHI: {analysis['phi']}")
print(f"Egyptian fraction 1/4 + 1/7 + 1/11 = {analysis['egyptian_fraction']}")

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

engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
new_state = engine.adjust_phase_delta(0.05)
print(f"After delta: {new_state}")  # PhaseState.STABILIZED
```

### Recursive Field Math (Lucas 4-7-11)

```python
from snell_vern_matrix import F, L, PHI, ratio, egypt_4_7_11, signature_summary

print(F(10))  # 55
print(L(5))   # 11 (Lucas: 2, 1, 3, 4, 7, 11, ...)
print(PHI)    # 1.618...
print(ratio(5))  # L(6)/L(5) approaches PHI

num, den = egypt_4_7_11()
print(f"{num}/{den}")

print(signature_summary())
```

### Recursive Field (Phyllotaxis)

```python
from snell_vern_matrix import golden_angle, radius, angle, position

ga = golden_angle()
print(f"Golden angle: {ga:.3f}°")

r = radius(5)       # 3 * sqrt(5) ≈ 6.708
r = radius(5, a=2)  # 2 * sqrt(5) ≈ 4.472

theta = angle(5)
x, y = position(10)
```

## Mathematical Background

### The Snell-Vern Framework

Extends classical recursive sequence theory by combining:

1. **Algebraic Number Theory**: Golden ratio φ and conjugate ψ.
2. **Symbolic Logic Processing**: Three-state (ternary) logic for glyph representation.
3. **Dynamical Systems**: Phase-state tracking with delta-based convergence.
4. **Combinatorial Number Theory**: Egyptian fractions and Frobenius numbers.

### Golden Ratio (φ) and Its Conjugate

The golden ratio φ satisfies φ² = φ + 1:

```
φ = (1 + √5) / 2 ≈ 1.618033988749895 (positive root)
ψ = (1 - √5) / 2 ≈ -0.618033988749895 (conjugate, negative root)
```

Properties:
- φ + ψ = 1
- φ × ψ = -1
- φⁿ and ψⁿ govern Fibonacci and Lucas sequences via Binet's formula.

### Golden Angle in Phyllotaxis

```
θ = 360° × (1 - 1/φ) = 360° × (2 - φ) = 180° × (3 - √5) ≈ 137.507764°
```

Appears in natural phyllotaxis (leaf arrangement) because it provides optimal packing without overlapping spirals.

### Lucas Numbers and Fibonacci Sequences

Fibonacci F(n):
```
F(0) = 0, F(1) = 1
F(n) = F(n-1) + F(n-2)
Sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...
Binet: F(n) = (φⁿ - ψⁿ) / √5
```

Lucas L(n):
```
L(0) = 2, L(1) = 1
L(n) = L(n-1) + L(n-2)
Sequence: 2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, ...
Closed form: L(n) = φⁿ + ψⁿ
```

Convergence:
```
lim(n→∞) F(n+1)/F(n) = φ
lim(n→∞) L(n+1)/L(n) = φ
```

Error bounds:
```
√5 / (Lₙ(Lₙ + |ψ|ⁿ)) ≤ |L(n+1)/L(n) - φ| ≤ √5 / (Lₙ(Lₙ - |ψ|ⁿ))
```

### Lucas 4-7-11 Signature

The triplet (L₃, L₄, L₅) = (4, 7, 11) exhibits useful properties:

Egyptian fraction:
```
1/4 + 1/7 + 1/11 = (77 + 44 + 28) / 308 = 149/308
```

Frobenius number:
```
F(4,7) = 4×7 - 4 - 7 = 17
```

Additive chain:
```
L₃ + L₄ = 4 + 7 = 11 = L₅
```

Applications:
- **Entropy generation**: 149/308 as a near-irrational approximation for pseudorandom sequences.
- **Cryptographic spacing**: Frobenius gaps create entropy pockets.
- **Field indexing**: Additive chain enables hierarchical field subdivision.

### Field Structures and Ternary Logic

The Field component models positions in a phyllotaxis arrangement:

```
r(n) = a√n
θ(n) = n × θ_golden (mod 360°)
x(n) = r(n) × cos(θ(n))
y(n) = r(n) × sin(θ(n))
```

Ternary logic states:
- State 0: Initial / Idle
- State 1: Processing / Active
- State 2: Stabilised / Complete

Enables:
- Balanced ternary arithmetic ({-1, 0, 1}).
- Three-valued logic.
- Symbolic glyph encoding.

### Glyph Symbolic Processing

```
Symbolic Input → Processing → Delta Adjustment → Stabilisation
     |              |               |                  |
  (Initial)    (Computing)   (Refinement)        (Converged)
```

Phase delta mechanism:
- |Δ| < 0.1: Converges to stabilisation.
- |Δ| > 1.0: Triggers error state.
- Moderate delta: Continues adjustment cycles.

### Entropy Sources

1. **Golden ratio irrationality**: continued fraction [1;1,1,1,1,...] provides unbounded randomness.
2. **Lucas ratio convergence**: near-chaotic behaviour in early terms before convergence.
3. **Phyllotaxis angular spacing**: near-uniform distribution avoiding resonances.
4. **Egyptian fraction approximations**: rational approximations to irrational targets.

Hygiene:
- All arithmetic uses exact integer operations (Fibonacci/Lucas via Binet).
- Floating-point used only for geometric visualisation.
- No hardcoded secrets or keys.
- Mathematical constants derived from first principles.

### Generating Functions

Fibonacci:
```
G_F(x) = Σ(n≥0) F(n)xⁿ = x / (1 - x - x²)
```

Lucas:
```
G_L(x) = Σ(n≥0) L(n)xⁿ = (2 - x) / (1 - x - x²)
```

Enables power series expansion, asymptotic analysis, and combinatorial identities.

## Testing

```bash
pytest                                          # all tests
pytest --cov=snell_vern_matrix --cov-report=html  # with coverage
pytest tests/test_drive_matrix.py               # specific file
pytest -v                                        # verbose
pytest -k "test_lucas"                          # by pattern
```

Current coverage: 38 tests across all major components.

## Tech Stack

- **Language**: Python 3.10+
- **Build System**: Hatchling (PEP 517)
- **Testing**: pytest with coverage
- **Linting**: Ruff
- **Type checking**: mypy
- **Dependencies**: zero runtime dependencies — pure Python core.

Design philosophy: lightweight, mathematically rigorous, dependency-free.

## Contributing

Areas of interest:

1. Extended sequences (Tribonacci, Pell numbers, etc.)
2. Visualisation tools (phyllotaxis plots, convergence graphs).
3. Performance optimisation (memoisation, matrix exponentiation for large n).
4. Additional applications (cryptographic protocols, pattern recognition).
5. Documentation (examples, tutorials, proofs).

Requirements:

- All tests pass (`pytest`).
- Code linted (`ruff check .`).
- Type hints (`mypy src/`).
- New features include tests and documentation.
- Commit messages follow [Conventional Commits](https://conventionalcommits.org):
  - `feat:`, `fix:`, `docs:`, `test:`, `chore:`

### Workflow

1. Fork the repo.
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make changes following conventional commits.
4. Run `pytest` and `ruff check . && ruff format .`
5. Push and open a Pull Request.
6. Ensure all CI checks pass (Build, Tests, Lint, Security).

## Publishing

### Python Package (PyPI)

Automated via GitHub Actions:

1. Push a semantic version tag (e.g. `v1.0.0`).
2. Workflow runs the test suite (≥80% coverage required), builds wheel + sdist, publishes via OIDC trusted publishing, and creates a GitHub release.
3. Manual publish: `python -m build && twine upload dist/*`

### JavaScript Package (npm) — ready for activation

When JavaScript/TypeScript files are added:

1. Add `package.json` with semantic-release config.
2. Set `NPM_TOKEN` repo secret.
3. Workflow activates on next push.

### Rust Package (crates.io) — ready for activation

When Rust files are added:

1. Add `Cargo.toml` with package metadata.
2. Set `CRATES_IO_TOKEN` repo secret.
3. Workflow publishes on tagged releases.

See [.github/workflows/](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/tree/main/.github/workflows) and [docs/CI_CD_PIPELINE.md](docs/CI_CD_PIPELINE.md).

## Security

- Automated scanning: Gitleaks, CodeQL, Bandit, pip-audit, OSSF Scorecard.
- Weekly scheduled vulnerability scans.
- Dependency review on all PRs.
- No hardcoded secrets — all credentials via GitHub Secrets.
- OIDC-based PyPI publishing.

Report security issues via [GitHub Security Advisories](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/security/advisories).

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2025 Adam Snellman (wizardaax)

## Contact

- **Author**: Adam Snellman (wizardaax)
- **Repository**: [github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)
- **Issues**: [Report bugs or request features](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/issues)

## Acknowledgments

This project merges and extends:

- [glyph_phase_engine](https://github.com/wizardaax/glyph_phase_engine) — symbolic input and phase processing.
- [recursive-field-math-pro](https://github.com/wizardaax/recursive-field-math-pro) — Lucas 4-7-11 sequences and mathematical foundations.
- [recursive-field-math](https://github.com/wizardaax/recursive-field-math) — phyllotaxis pattern formulas.

## References

- Knuth, D. E. *The Art of Computer Programming, Volume 1: Fundamental Algorithms* (Fibonacci and Lucas numbers).
- Vogel, H. *A better way to construct the sunflower head* (phyllotaxis mathematics).
- Hardy, G. H. & Wright, E. M. *An Introduction to the Theory of Numbers* (golden ratio properties).

Related projects:

- [SymPy](https://www.sympy.org/) — symbolic mathematics in Python.
- [OEIS](https://oeis.org/) — Online Encyclopedia of Integer Sequences (Fibonacci: A000045, Lucas: A000032).
