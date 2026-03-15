# Compatibility Matrix

This document records the tested compatibility surface of the
**Snell-Vern Hybrid Drive Matrix** library and its CI/CD toolchain.

## Python runtime compatibility

| Python version | Status | Notes |
|---|---|---|
| 3.10 | ✅ Supported | Minimum supported version |
| 3.11 | ✅ Supported | Fully tested in CI matrix |
| 3.12 | ✅ Supported (primary) | Used for coverage & publishing |
| 3.13+ | 🔲 Untested | Not yet in CI matrix |

## Operating system compatibility

| OS | Status | Notes |
|---|---|---|
| Ubuntu (latest) | ✅ Supported | Primary CI runner; used for coverage |
| Windows (latest) | ✅ Supported | Tested in CI matrix |
| macOS (latest) | ✅ Supported | Tested in CI matrix |

## Dependency compatibility

| Dependency | Version constraint | Runtime / Dev |
|---|---|---|
| Python | `>=3.10` | Runtime |
| pytest | `>=7.0` | Dev |
| pytest-cov | any | Dev |
| ruff | any | Dev |
| mypy | any | Dev |
| build | any | Dev |
| hatchling | any | Build |
| twine | any | Build |

Runtime core: **zero external runtime dependencies** (pure Python).

## aeon-standards workflow compatibility

| aeon-standards ref | Compatible | Notes |
|---|---|---|
| `@v1` | ✅ | Current pinned version |

## GitHub Actions runner compatibility

| Runner | Status |
|---|---|
| `ubuntu-latest` | ✅ |
| `windows-latest` | ✅ |
| `macos-latest` | ✅ |

## CI workflow file compatibility

| Workflow | Trigger branches | paths-ignore |
|---|---|---|
| `build.yml` | `main`, `develop` | `**/*.pdf`, `**/*.docx` |
| `lint.yml` | `main`, `develop` | `**/*.pdf`, `**/*.docx` |
| `test.yml` | `main`, `develop` | `**/*.pdf`, `**/*.docx` |
| `aeon-python-ci.yml` | `main`, `develop` | `**/*.pdf`, `**/*.docx` |
| `aeon-security.yml` | `main`, `develop` + weekly schedule | `**/*.pdf`, `**/*.docx` |
| `security.yml` | `main`, `develop` + weekly schedule | — |
| `release.yml` | tags `v*.*.*` | — |
| `node.yml` | `main`, `develop` | — |
| `rust.yml` | `main`, `develop` | — |
| `conventional-commits.yml` | PR events | — |
