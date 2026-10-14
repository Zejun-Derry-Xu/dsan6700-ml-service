---
name: Bug report
about: Report a reproducible problem with the Iris API, configuration, or deployment.
title: '[Bug] '
labels: ''
assignees: ''
---

## Problem

Describe what is failing and how it affects use of the service.

## Affected area

- [ ] `GET /health`
- [ ] `POST /predict` or prediction input validation
- [ ] Settings or application startup
- [ ] Model training or artifact loading
- [ ] Docker, Compose, or Jetstream2 recovery
- [ ] Tests or CI
- [ ] Other (describe below)

## Steps to reproduce

1. State the commit or branch and how the service was started.
2. Include the exact command or request that triggers the problem.
3. Describe the result.

For prediction problems, include the four measurement values in centimeters
and any unexpected fields. A valid example is:

```json
{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}
```

## Expected behavior

Describe the expected HTTP status, response, or startup behavior.
For the standard trained model, the example above should return class 0,
`setosa`. Invalid measurements should return HTTP 422.

## Actual behavior and evidence

Include the HTTP status and response, traceback, relevant CI run link, or
container log excerpt. For Docker failures, include `docker compose ps`
and relevant output from `docker compose logs --tail 50 api`.
Remove secrets and credentials before posting logs or configuration.

## Environment

- Commit or branch:
- Run mode: local Uvicorn / local Compose / Jetstream2 Compose
- Operating system and CPU architecture:
- Python and uv versions, or Docker and Compose versions:
- Relevant non-secret setting values, including `INFERENCE_DELAY_SECONDS`:
- For model-loading failures: `MODEL_PATH` and the command used to create it:

## Proposed fix (optional)

Describe a possible cause or fix, if known.
