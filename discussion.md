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
`blocking-baseline`; the tag must be pushed to make it available remotely.
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
