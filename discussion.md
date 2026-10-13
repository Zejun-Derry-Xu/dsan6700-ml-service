# Request execution and blocking-call audit

## Steps for one prediction request

The local Iris classifier uses StandardScaler followed by LogisticRegression.
The artifact is loaded once at application startup and reused across requests.
No external model service, database, or cache is involved in inference.

Real inference is too fast to illustrate blocking clearly. This experiment
therefore adds `time.sleep(2)` before the real prediction as an artificial
stand-in for a slow synchronous call. Normal operation uses
`INFERENCE_DELAY_SECONDS=0`.

| Step | Computing or waiting? | On what? | Approximate duration |
| --- | --- | --- | --- |
| Receive and parse the request | Waiting, then computing | Local connection bytes, HTTP and JSON parsing | Small overhead; not separately measured |
| Validate the input | Computing | Pydantic parses the four measurement fields | Small overhead; not separately measured |
| Resolve the client and schedule the handler | Computing, possibly waiting | Existing model client and thread-pool scheduling | Small overhead at this load; not separately measured |
| Simulate slow inference | Waiting | Worker thread waits for the sleep timer | Approximately 2 seconds |
| Run the real model | Computing | Order features, standardize, classify, and map the class ID to its name | Small overhead for one sample; not separately measured |
| Encode and send the response | Computing, then potentially waiting | Response validation, JSON encoding, and connection writes | Small overhead; not separately measured |

The table describes the fixed version. A worker thread remains occupied
while sleeping, but the event loop can process other requests. Training and
artifact loading are not repeated for each prediction.

Fixed request times ranged from 2.0080 to 2.0223 seconds as observed by the
client. Time above the configured 2-second delay combines client, server,
scheduling, model, and transport overhead. Individual stages were not
instrumented, so their precise times are not claimed.

## Measured before and after

Both runs used one Uvicorn worker, `INFERENCE_DELAY_SECONDS=2`, the same
payload, and ten concurrent requests using `httpx.AsyncClient` and
`asyncio.gather`. One warm-up request was excluded from the timed interval.
All ten measured requests returned HTTP 200 and class `setosa`.

| Version | Total wall-clock time for 10 requests | Slowest request |
| --- | ---: | ---: |
| Blocking async def handler | 20.0790 seconds | 20.0773 seconds |
| Fixed plain def handler | 2.0239 seconds | 2.0223 seconds |

Raw results are in `benchmarks/blocking.json` and `benchmarks/fixed.json`.

The blocking handler ran synchronous sleep and model inference directly
on the event loop, preventing other requests from progressing during each
sleep. A plain `def` handler runs in FastAPI's worker thread pool, allowing
the ten waits to overlap. Total time decreased by approximately 9.9 times
in this experiment; model computation itself did not become faster.

This demonstrates responsiveness during synchronous waiting at the tested
load. The thread pool has finite capacity; this is not evidence of unlimited
concurrency or faster CPU-bound model computation.

## Reproduction

Follow README.md for installing the locked development dependencies and
training the model. The blocking version is preserved under Git tag
`blocking-baseline`, which is published in the remote repository.
README.md provides a separate-checkout procedure for reproducing that version.

Start either version with:

```bash
INFERENCE_DELAY_SECONDS=2 \
uv run uvicorn dsan6700_ml_service.api:app --workers 1
```

In another terminal in the same checkout, run:

```bash
uv run python scripts/benchmark_concurrency.py \
  --label blocking \
  --output benchmarks/blocking.json
```

For the fixed version use `--label fixed` and
`--output benchmarks/fixed.json`. Stop and restart the server when switching
versions. Each benchmark includes a warm-up before the ten timed requests.

## Responsiveness regression test

`tests/test_responsiveness.py` injects a controlled slow model, starts a
prediction, and waits for the model to signal that inference has begun.
It requires `/health` to return HTTP 200 within one second while the
prediction remains unfinished. It then releases inference and checks the
prediction response. No real artifact or external server is needed.


## Docker packaging and build measurements

The image installs runtime dependencies from uv.lock using
uv sync --frozen before copying the application source. This allows
the dependency layer to be reused when only source code changes.

The Iris model is generated during the image build and loaded once
at application startup. The container runs as the non-root app user
and includes a health check against /health.

Measurements were taken on the team's Jetstream2 instance (Ubuntu
24.04, x86_64, Docker Engine 29.1.3, Docker Compose 2.40.3) with
`scripts/measure_docker.sh` at commit `cf0acf3`. The script appended
one comment line to `src/dsan6700_ml_service/__init__.py`, timed both
rebuilds against that same modified source, then restored the file and
started the stack from the committed source.

| Measurement | Result |
| --- | ---: |
| Image disk usage reported by docker image ls | 595 MB |
| Image content size | 141 MB (141,234,463 bytes) |
| Rebuild with cached dependency layer | 6.78 seconds |
| Rebuild with --no-cache | 20.54 seconds |

Build times are wall-clock seconds around `docker compose build`.
The cached rebuild was approximately 3.0 times faster: only the
layers from `COPY src/` onward were rebuilt, while the `uv sync`
dependency layer was reused. The --no-cache run repeated every build
instruction but did not download the base images again.

The docker system df snapshot after the stack was up was:

```text
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          5         5         2.811GB   2.811GB (100%)
Containers      5         4         27.13MB   12.29kB (0%)
Local Volumes   1         1         270.8MB   0B (0%)
Build Cache     31        0         1.071GB   476.5MB
```

This snapshot covers the entire Docker installation on the instance,
including other containers and images on it. It is not the disk usage
of this service alone.

## Deployment on Jetstream2

The stack was started on the instance from a clone of the repository
with Compose. The container reported `healthy` and runs as
`uid=10001(app)`. Requests sent from a computer outside the instance to
`http://149.165.169.189:8000` returned:

| Request | Response |
| --- | --- |
| `GET /health` | HTTP 200, `{"status":"healthy"}` |
| `POST /predict` with valid measurements | HTTP 200, `{"class_id":0,"class_name":"setosa"}` |
| `POST /predict` with `sepal_length` of -1 | HTTP 422, `greater_than` |
| `POST /predict` with an unexpected field | HTTP 422 |

The Compose stack contains only the API service. It requires no
database, cache, or external model service. There is no mutable
application data requiring a named volume; the model is included
in the image. Compose configures restart: unless-stopped.
