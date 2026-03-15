# Engineering Standards

This document captures the governance conventions for the
**Snell-Vern Hybrid Drive Matrix** repository, including the federated
CI/CD wiring introduced during the *aeon-standards* migration.

## aeon-standards federation

All federated workflows in this repository delegate to reusable workflows
published in the [wizardaax/aeon-standards](https://github.com/wizardaax/aeon-standards)
shared-workflow library.

### Pinned reference

| Workflow file | Reusable caller target | Pinned ref |
|---|---|---|
| `.github/workflows/aeon-python-ci.yml` | `wizardaax/aeon-standards/.github/workflows/python-ci.yml` | `@v1` |
| `.github/workflows/aeon-security.yml` | `wizardaax/aeon-standards/.github/workflows/security.yml` | `@v1` |

**Rule**: All `uses:` references to `wizardaax/aeon-standards` **must** be
pinned to a semantic version tag (`@v1`, `@v2`, …) or a full commit SHA.
Floating refs (`@main`, `@HEAD`) are prohibited in production branches.

### Upgrading the pinned ref

1. Review the aeon-standards [CHANGELOG](https://github.com/wizardaax/aeon-standards/blob/main/CHANGELOG.md)
   for breaking changes.
2. Update every `@vN` occurrence in the two federated workflow files.
3. Open a PR with title `ci: upgrade aeon-standards to @vN+1`.
4. Ensure all required checks pass before merging.

## Branch protection required checks

The following workflow job contexts are treated as **stable required checks**
(i.e., they must pass before any PR can be merged into `main`):

- `Build Package` (from `build.yml`)
- `Code Quality Checks` (from `lint.yml`)
- `Test Suite (Python 3.12 on ubuntu-latest)` (from `test.yml`)
- `Python CI (aeon-standards@v1)` (from `aeon-python-ci.yml`)
- `Security (aeon-standards@v1)` (from `aeon-security.yml`)
- `Validate PR Title` (from `conventional-commits.yml`)

Dynamic matrix-generated job names (e.g. varying OS/version combinations)
**must not** be used as required checks because they break when the matrix
changes.

## Noise-reduction policy

QA workflows (`build.yml`, `lint.yml`, `test.yml`, `aeon-python-ci.yml`,
`aeon-security.yml`) include `paths-ignore` rules that skip runs triggered
solely by documentation binary changes:

```yaml
paths-ignore:
  - '**/*.pdf'
  - '**/*.docx'
```

This prevents spurious CI runs caused by committing PDF/DOCX design
artefacts to the repository.

## Commit message convention

All commits must follow [Conventional Commits 1.0.0](https://conventionalcommits.org).
The `conventional-commits.yml` workflow enforces this automatically on every PR.

## Security scanning cadence

| Scanner | Trigger |
|---|---|
| Gitleaks (secret detection) | Push / PR |
| Dependency Review | PR only |
| pip-audit | Push / PR |
| CodeQL (Python) | Push / PR |
| Bandit | Push / PR |
| OSSF Scorecard | Push to `main` + weekly schedule |
| aeon-standards security suite | Push / PR + weekly schedule |
