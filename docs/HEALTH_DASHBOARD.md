# Health Dashboard

This document provides a snapshot of the operational health indicators for the
**Snell-Vern Hybrid Drive Matrix** repository.

## CI/CD status

| Workflow | Badge |
|---|---|
| Build | [![Build](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Build/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/build.yml) |
| Tests | [![Tests](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Tests/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/test.yml) |
| Lint | [![Lint](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Lint/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/lint.yml) |
| Security | [![Security](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Security/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/security.yml) |
| Aeon Python CI | [![Aeon Python CI](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Aeon%20Python%20CI/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/aeon-python-ci.yml) |
| Aeon Security | [![Aeon Security](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Aeon%20Security/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/aeon-security.yml) |

## Code quality

| Metric | Target | Source |
|---|---|---|
| Test coverage | ≥ 80 % | Codecov |
| Lint violations | 0 | Ruff |
| Type errors | 0 warnings | mypy |
| Security findings | 0 high/critical | Bandit + CodeQL |

[![codecov](https://codecov.io/gh/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/branch/main/graph/badge.svg)](https://codecov.io/gh/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)

## Security posture

| Scanner | Schedule | Last known status |
|---|---|---|
| Gitleaks | Push / PR | See Actions tab |
| pip-audit | Push / PR | See Actions tab |
| CodeQL | Push / PR | See Security tab |
| Bandit | Push / PR | See Actions tab |
| OSSF Scorecard | Push to `main` + weekly | [![OSSF Scorecard](https://api.scorecard.dev/projects/github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/badge)](https://scorecard.dev/viewer/?uri=github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix) |
| aeon-standards security | Push / PR + weekly | See Actions tab |

## Governance

| Standard | Ref | Documentation |
|---|---|---|
| aeon-standards | `@v1` | [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) |
| Conventional Commits | 1.0.0 | [conventionalcommits.org](https://conventionalcommits.org) |

[![Aeon Standards](https://img.shields.io/badge/aeon--standards-v1-blueviolet.svg)](https://github.com/wizardaax/aeon-standards)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

## Release health

| Channel | Latest | Badge |
|---|---|---|
| PyPI | see badge | [![PyPI](https://img.shields.io/pypi/v/snell-vern-matrix)](https://pypi.org/project/snell-vern-matrix/) |
| License | MIT | [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE) |

## Noise-reduction status

PDF and DOCX files in the repository no longer trigger QA CI runs.
The following `paths-ignore` rule is applied to `build.yml`, `lint.yml`,
`test.yml`, `aeon-python-ci.yml`, and `aeon-security.yml`:

```yaml
paths-ignore:
  - '**/*.pdf'
  - '**/*.docx'
```

See [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) for the full
noise-reduction policy.
