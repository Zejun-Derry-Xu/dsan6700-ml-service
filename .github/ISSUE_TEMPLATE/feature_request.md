---
name: Feature request
about: Propose a scoped improvement to the Iris classification service.
title: '[Feature] '
labels: ''
assignees: ''
---

## Problem or use case

Who needs this change, and what can they not do with the current service?

## Proposed behavior

Describe the requested behavior. If an API change is needed, show the
request fields, units, response, and HTTP status with a small example.
Explain any effect on the existing `/health` and `/predict` endpoints.

## Scope and implementation

- Application modules or supporting files expected to change:
- Settings or model-artifact changes, if any:
- Dependency or Docker/Compose changes, if any:
- Work intentionally outside this issue:

Coordinate shared-file or dependency changes with the relevant teammate.

## Alternatives and tradeoffs

Describe simpler alternatives and relevant effects on startup time,
responsiveness, model compatibility, or deployment complexity.

## Acceptance criteria

Replace these prompts with observable checks for this feature:

- [ ] The requested behavior is demonstrated with a concrete example.
- [ ] Relevant tests cover the behavior and failure cases.
- [ ] Existing valid predictions and health checks remain compatible,
      or a deliberate compatibility change is documented.
- [ ] Ruff, formatting, Mypy, Pytest, and CI pass.
- [ ] README or discussion updates are included when behavior or operation changes.

## Collaboration

- Proposed owner:
- Related issues or dependent PRs:
- Create a feature branch and link the implementation PR to this issue.
- Request a teammate review before merging; close the issue when completed.
