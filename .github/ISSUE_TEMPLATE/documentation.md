---
name: Documentation improvement
about: Report missing or unclear setup, API, experiment, or deployment instructions.
title: '[Docs] '
labels: ''
assignees: ''
---

## Document and location

Link to the file and heading that needs a change, such as `README.md`
(local setup or Jetstream2 deployment) or `discussion.md` (measurements).
Include the commit or branch you were following.

## Missing or unclear information

Explain what is incorrect, incomplete, or difficult to follow.
If a command failed, include the exact command and relevant error output.
Remove secrets and credentials before sharing output.

## Intended reader and environment

Who needs this instruction, and where are they running it?
For example: a teammate on macOS using Docker Desktop, or a grader on a
fresh Ubuntu Jetstream2 instance.

## Proposed change

Describe the explanation, command, example, or measured result to add.
For measurements, state the host, method, units, and actual result;
distinguish local measurements from instance measurements.

## Acceptance criteria

- [ ] The affected instructions and expected outputs are clear.
- [ ] Commands use the correct working directory and prerequisites.
- [ ] Another team member can follow the changed steps where applicable.
- [ ] Results described as verified were actually tested; pending checks
      are identified as pending.

## Related work (optional)

Link to related issues, PRs, CI runs, or reproduction evidence.
