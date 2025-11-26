# GitHub Actions Workflow Status

This document provides a quick reference for all automated workflows in this repository.

## Active Python Workflows

| Workflow | Status | Trigger | Purpose |
|----------|--------|---------|---------|
| **Build** | ✅ Active | Push/PR to main/develop | Verify package builds correctly |
| **Test** | ✅ Active | Push/PR to main/develop | Run test suite on multiple platforms |
| **Lint** | ✅ Active | Push/PR to main/develop | Code quality and formatting checks |
| **Release** | ✅ Active | Tag push (v*.*.*) | Automated PyPI publishing |
| **Security** | ✅ Active | Push/PR/Weekly | Security scanning and auditing |
| **Conventional Commits** | ✅ Active | Pull requests | Validate commit message format |

## Placeholder Workflows (Ready for Activation)

| Workflow | Status | Activation Trigger | Purpose |
|----------|--------|-------------------|---------|
| **Node.js** | 🟡 Placeholder | Add package.json | JavaScript/TypeScript CI/CD |
| **Rust** | 🟡 Placeholder | Add Cargo.toml | Rust CI/CD |

## Workflow Details

### Build (`build.yml`)
- **Python Version**: 3.12
- **Platforms**: Ubuntu
- **Outputs**: Wheel and sdist artifacts
- **Cache**: pip dependencies
- **Auto-cancel**: Yes

### Test (`test.yml`)
- **Python Versions**: 3.10, 3.11, 3.12
- **Platforms**: Ubuntu, Windows, macOS
- **Coverage**: Uploaded to Codecov
- **Reports**: HTML coverage artifacts
- **Auto-cancel**: Yes

### Lint (`lint.yml`)
- **Tools**: Ruff (linter + formatter), mypy
- **Python Version**: 3.12
- **Platform**: Ubuntu
- **Auto-cancel**: Yes

### Release (`release.yml`)
- **Stages**:
  1. Pre-publish tests (≥80% coverage required)
  2. Build distributions
  3. Publish to PyPI (trusted publishing/OIDC)
  4. Create GitHub release
- **Artifacts**:
  - Python distributions (wheel, sdist)
  - Coverage report (XML)
  - Coverage badge (SVG)
  - CHANGELOG.md
- **Auto-cancel**: Yes

### Security (`security.yml`)
- **Tools**:
  - Gitleaks (secret scanning)
  - Dependency Review (PR only)
  - pip-audit (Python packages)
  - CodeQL (static analysis)
  - Bandit (Python security)
  - OSSF Scorecard (best practices)
- **Schedule**: Weekly (Mondays 00:00 UTC)
- **Platforms**: Ubuntu
- **Auto-cancel**: Yes

### Conventional Commits (`conventional-commits.yml`)
- **Validates**:
  - PR title format
  - Commit message format
- **Provides**: Helpful guidance on failures
- **Auto-cancel**: Yes

### Node.js (`node.yml`) - PLACEHOLDER
- **Auto-detection**: Checks for package.json or .js/.ts files
- **Features**:
  - ESLint linting
  - Jest testing (Node 18, 20, 22)
  - Cross-platform builds
  - Semantic-release to npm
- **Status**: Inactive until JavaScript files detected

### Rust (`rust.yml`) - PLACEHOLDER
- **Auto-detection**: Checks for Cargo.toml or .rs files
- **Features**:
  - Clippy linting
  - rustfmt formatting
  - cargo test (stable, beta)
  - cargo-audit security
  - crates.io publishing
- **Status**: Inactive until Rust files detected

## Secrets Required

### Currently Active
- `GITHUB_TOKEN` - Auto-provided by GitHub Actions
- `CODECOV_TOKEN` - Optional, for Codecov uploads

### For PyPI Publishing
- **Recommended**: Set up [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- **Alternative**: Set `PYPI_API_TOKEN` secret

### For Future Use
- `NPM_TOKEN` - For npm publishing (when JavaScript added)
- `CRATES_IO_TOKEN` - For crates.io publishing (when Rust added)
- `GITLEAKS_LICENSE` - Optional, for Gitleaks Pro features

## Badge URLs

Add these to README.md for visual status indicators:

```markdown
<!-- Build Status -->
[![Build](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Build/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/build.yml)
[![Tests](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Tests/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/test.yml)
[![Lint](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Lint/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/lint.yml)
[![Security](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/workflows/Security/badge.svg)](https://github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/actions/workflows/security.yml)

<!-- Coverage -->
[![codecov](https://codecov.io/gh/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/branch/main/graph/badge.svg)](https://codecov.io/gh/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)

<!-- Package -->
[![PyPI](https://img.shields.io/pypi/v/snell-vern-matrix)](https://pypi.org/project/snell-vern-matrix/)

<!-- Security -->
[![OSSF Scorecard](https://api.scorecard.dev/projects/github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix/badge)](https://scorecard.dev/viewer/?uri=github.com/wizardaax/Snell-Vern-Hybrid-Drive-Matrix)
```

## Troubleshooting

### Workflow Not Running
- Check if workflow trigger matches your action (push, PR, tag)
- Verify workflow file is in `.github/workflows/` directory
- Check workflow file is valid YAML

### Failed Workflow
- Click on failed workflow in Actions tab
- Expand failed step to see error details
- Check logs for specific error messages

### Coverage Upload Fails
- Verify `CODECOV_TOKEN` is set (optional but recommended)
- Check Codecov.io for account and repository setup

### Release Publish Fails
- Verify version tag format: `v1.0.0` (semantic versioning)
- Check PyPI credentials or trusted publishing setup
- Ensure version doesn't already exist on PyPI

## Monitoring

- **Actions Tab**: View all workflow runs
- **Security Tab**: Review security alerts and Scorecard
- **Insights**: Dependency graph and security alerts
- **Codecov**: Track coverage trends over time

## Best Practices

1. **Always use conventional commits** for automated versioning
2. **Tag releases** with semantic versions (v1.0.0)
3. **Update CHANGELOG.md** before releases
4. **Monitor security alerts** weekly
5. **Keep dependencies updated** regularly
6. **Review failed workflows** promptly
7. **Use draft releases** for testing release process

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

Last updated: 2025-11-26
