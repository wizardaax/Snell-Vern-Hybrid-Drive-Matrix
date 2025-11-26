# CI/CD Pipeline Documentation

This document describes the comprehensive CI/CD automation for the Snell-Vern Hybrid Drive Matrix project, supporting Python, JavaScript, and Rust.

## Table of Contents

- [Overview](#overview)
- [Python Pipeline](#python-pipeline)
- [JavaScript Pipeline](#javascript-pipeline)
- [Rust Pipeline](#rust-pipeline)
- [Security Scanning](#security-scanning)
- [Conventional Commits](#conventional-commits)
- [Best Practices](#best-practices)

## Overview

The project implements fully automated CI/CD pipelines with the following features:

- ✅ **Cross-platform testing** (Ubuntu, Windows, macOS)
- ✅ **Automated publishing** to package registries (PyPI, npm, crates.io)
- ✅ **Security scanning** (secrets, vulnerabilities, code analysis)
- ✅ **Code quality checks** (linting, formatting, type checking)
- ✅ **Coverage reporting** with badge generation
- ✅ **Conventional commit enforcement**
- ✅ **Auto-cancellation** of obsolete workflow runs
- ✅ **Dependency caching** for faster builds

## Python Pipeline

### Active Workflows

#### Build (`build.yml`)
- **Trigger**: Push or PR to `main`/`develop`
- **Purpose**: Verify package builds correctly
- **Steps**:
  1. Build wheel and sdist with hatch
  2. Verify with twine check
  3. Upload build artifacts
- **Status**: ✅ Active

#### Test (`test.yml`)
- **Trigger**: Push or PR to `main`/`develop`
- **Matrix**: Python 3.10, 3.11, 3.12 × Ubuntu, Windows, macOS
- **Steps**:
  1. Run pytest with verbose output
  2. Generate coverage report (XML, HTML, terminal)
  3. Upload coverage to Codecov
- **Coverage Required**: ≥80% for releases
- **Status**: ✅ Active

#### Lint (`lint.yml`)
- **Trigger**: Push or PR to `main`/`develop`
- **Steps**:
  1. Run Ruff linter (code issues)
  2. Run Ruff formatter (code style)
  3. Run mypy type checker (informational)
- **Status**: ✅ Active

#### Release (`release.yml`)
- **Trigger**: Push semantic version tag (`v*.*.*`)
- **Jobs**:
  1. **test-before-publish**: Run tests with ≥80% coverage requirement
  2. **build**: Build wheel and sdist
  3. **publish-pypi**: Publish to PyPI using trusted publishing (OIDC)
  4. **github-release**: Create GitHub release with artifacts
- **Artifacts Included**:
  - Python distributions (wheel, sdist)
  - Coverage report (XML)
  - Coverage badge (SVG)
  - CHANGELOG.md
- **Authentication**: Trusted publishing (no API tokens)
- **Status**: ✅ Active

### Publishing to PyPI

#### Automatic Publishing
```bash
# Tag a release with semantic version
git tag v1.0.0
git push origin v1.0.0

# Workflow automatically:
# 1. Runs tests with coverage validation
# 2. Builds distributions
# 3. Publishes to PyPI
# 4. Creates GitHub release
```

#### Manual Publishing (if needed)
```bash
# Install build tools
pip install build twine

# Build distributions
python -m build

# Check distributions
twine check dist/*

# Upload to PyPI (requires PYPI_API_TOKEN)
twine upload dist/*
```

## JavaScript Pipeline

### Placeholder Workflow (`node.yml`)

**Status**: 🟡 Ready for activation (placeholder)

The workflow auto-activates when `package.json` or `.js`/`.ts` files are detected.

See full documentation in the workflow file at `.github/workflows/node.yml`

## Rust Pipeline

### Placeholder Workflow (`rust.yml`)

**Status**: 🟡 Ready for activation (placeholder)

The workflow auto-activates when `Cargo.toml` or `.rs` files are detected.

See full documentation in the workflow file at `.github/workflows/rust.yml`

## Security Scanning

### Security Workflow (`security.yml`)

**Trigger**: Push, PR, weekly schedule (Mondays), manual

#### Security Jobs

1. **secret-scanning** (Gitleaks) - Scans for hardcoded secrets
2. **dependency-review** - Reviews dependency changes in PRs
3. **pip-audit** - Audits Python packages for vulnerabilities
4. **codeql** - Static code analysis for security issues
5. **bandit** - Python security linting
6. **scorecard** (OSSF) - Security best practices evaluation

## Conventional Commits

### Workflow (`conventional-commits.yml`)

Ensures all commits follow conventional commit format for automated versioning.

#### Valid Types

- `feat`: New feature (minor version bump)
- `fix`: Bug fix (patch version bump)
- `docs`: Documentation changes
- `style`: Code style/formatting
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks
- `revert`: Revert previous commit

#### Examples

```bash
feat: add automated PyPI publishing workflow
fix(ci): correct coverage report upload path
docs: update README with workflow badges
chore(deps): update GitHub Actions to v4
```

## Best Practices

### Release Workflow

1. Ensure all tests pass locally
2. Update CHANGELOG.md with new version section
3. Commit: `chore: prepare release v1.0.0`
4. Tag: `git tag v1.0.0`
5. Push: `git push origin v1.0.0`
6. Workflow handles rest automatically!

### Security Practices

- ✅ Use GitHub Secrets, never hardcode
- ✅ OIDC trusted publishing where possible
- ✅ Minimal permissions
- ✅ Regular dependency updates
- ✅ Multi-layer security scanning

For complete documentation, see individual workflow files in `.github/workflows/`
