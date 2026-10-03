# DSAN 6700 ML Service

A FastAPI classification service built for DSAN 6700 by Peipei Ji,
Shuchen Liu, and Zejun Xu. Homework 2 continues the project from Homework 1
in the same repository.

## Current Features

- Installable Python package and locked dependencies managed with `uv`.
- Environment configuration with Pydantic Settings.
- A trained Iris classifier: `StandardScaler` and `LogisticRegression`.
- Model loading once per application startup and reuse across requests.
- `GET /health` and `POST /predict` endpoints.
- API tests using an injected fake model client.
- A measured concurrency audit and a health responsiveness regression test.
- Ruff, Mypy, Pytest, pre-commit, and GitHub Actions.

## Project Structure

```text
.
├── .env.development.example
├── .env.production.example
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── uv.lock
├── README.md
├── scripts/
│   ├── train_model.py
│   └── benchmark_concurrency.py
├── benchmarks/
│   ├── blocking.json
│   └── fixed.json
├── discussion.md
├── artifacts/
│   └── iris.joblib             # Generated locally; ignored by Git
├── src/dsan6700_ml_service/
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   ├── model_client.py
│   └── schemas.py
└── tests/
    ├── test_api.py
    ├── test_config.py
    └── test_responsiveness.py
```

## Local Setup and Run Instructions

### 1. Check the Required Tools

Install Git and `uv`. The project requires Python 3.12 or later; CI runs
on Python 3.12, which is also specified in `.python-version`.

```bash
git --version
uv --version
```

### 2. Clone the Repository

```bash
git clone https://github.com/Zejun-Derry-Xu/dsan6700-ml-service.git
cd dsan6700-ml-service
```

Run the remaining setup and server commands from the repository root.
To review the current concurrency-audit work before it is merged, switch
to its branch:

```bash
git switch feature/nonblocking-inference
```

### 3. Install Dependencies

```bash
uv sync --extra dev --frozen
uv run pre-commit install
```

`--frozen` installs the versions recorded in `uv.lock`. The `dev` extra
includes the tools used for tests and code-quality checks.

### 4. Configure the Application

Settings are defined in `src/dsan6700_ml_service/config.py` and read
during application startup.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `DSAN 6700 ML Service` | Application title |
| `APP_ENV` | `development` | One of `development`, `testing`, or `production` |
| `LOG_LEVEL` | `INFO` | Logging-level setting; accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `MODEL_PATH` | `artifacts/iris.joblib` | Saved model artifact to load |
| `INFERENCE_DELAY_SECONDS` | `0.0` | Artificial synchronous delay before real inference, in seconds; use 0 for normal operation |

The application reads `.env` from the working directory when it exists.
Environment variables override values in `.env`; otherwise defaults apply.
The example files are templates, so their names are not loaded directly.

Default settings are sufficient for the commands below. To create an
optional development configuration, copy the example if you do not
already have a `.env` file:

```bash
cp .env.development.example .env
```

The new model settings can be added to that file when needed:

```dotenv
MODEL_PATH=artifacts/iris.joblib
INFERENCE_DELAY_SECONDS=0
```

Relative model paths resolve from the working directory. Keep real
environment files and secrets out of Git. The example files must contain
example values only. Existing application validators reject invalid
configuration such as an unsupported `APP_ENV` or a blank `APP_NAME`.
Additional model-configuration validation is a follow-up team task.

### 5. Generate the Model

```bash
uv run python scripts/train_model.py
```

The script loads the Iris dataset, makes a stratified 80/20 training/test
split with seed 42, and trains a standardization/classification pipeline.
It prints the held-out test accuracy and verifies a prediction after
reloading the saved artifact.

`artifacts/iris.joblib` contains the fitted pipeline, class names, input
feature order, and artifact format version. The directory is ignored by
Git, so a fresh clone must generate the model before starting the service.
Training and serving use the same locked dependency environment.

To choose another output location, generate the artifact there and set
`MODEL_PATH` to the same path:

```bash
uv run python scripts/train_model.py --output artifacts/another_model.joblib
```

### 6. Start the Service

```bash
uv run uvicorn dsan6700_ml_service.api:app
```

Startup reads the settings and loads the real model once for this
application process. Requests reuse that client. A missing model file
causes startup to fail. Keep this terminal running and use a second
terminal for the endpoint calls below. Press `Ctrl+C` to stop the service.

Interactive API documentation: <http://127.0.0.1:8000/docs>.

### 7. Call the Endpoints

Check service health:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

The health endpoint reports that the application is responding; it does
not perform a prediction.

Predict the Iris class from four measurements in centimeters:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'
```

Expected response with the generated model:

```json
{"class_id":0,"class_name":"setosa"}
```

All four input fields are required. They are assembled in the training
order: sepal length, sepal width, petal length, petal width. The model
classes are `0 = setosa`, `1 = versicolor`, and `2 = virginica`.

The current schema validates required fields and float conversion.
Stricter measurement and unknown-field validation is a follow-up team task.

## Quality Checks and Tests

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest
uv run pre-commit run --all-files
```

The current four tests cover:

- The `/health` status and response.
- `/predict` passing measurements to an injected fake client and returning
  its result, even when `MODEL_PATH` points to a missing file.
- Rejection of an invalid `APP_ENV` value.
- `/health` responding while an injected slow prediction remains pending.

Tests do not require the generated model artifact. `create_app` accepts a
fake client. API tests use `with TestClient(...)`; the concurrency test
uses `httpx.ASGITransport` and an explicit application lifespan context.

## Continuous Integration

`.github/workflows/ci.yml` runs on every push and pull request. It installs
dependencies from `uv.lock` and runs Ruff lint, Ruff formatting, Mypy, and
Pytest. Check that the workflow is green before merging a PR.

## Concurrency Audit

The Iris classifier answers quickly, so the audit adds a configurable
`time.sleep(2)` before the real prediction to demonstrate blocking.
The fixed `/predict` handler uses plain `def`, so FastAPI executes the
synchronous work in its worker thread pool.

After local setup and model generation, start a single-worker server:

```bash
INFERENCE_DELAY_SECONDS=2 \
uv run uvicorn dsan6700_ml_service.api:app --workers 1
```

In a second terminal at the repository root, send ten concurrent requests:

```bash
uv run python scripts/benchmark_concurrency.py \
  --label fixed \
  --output benchmarks/fixed.json
```

The script excludes one warm-up request and checks all prediction results.
The recorded local measurements are:

| Version | Total time for 10 requests | Slowest request |
| --- | ---: | ---: |
| Blocking `async def` | 20.0790 seconds | 20.0773 seconds |
| Fixed plain `def` | 2.0239 seconds | 2.0223 seconds |

See [discussion.md](discussion.md) for the request-step table, explanation,
and reproduction instructions. Raw measurements are in `benchmarks/`.
The blocking version is preserved locally under the `blocking-baseline`
Git tag; publish it with `git push origin blocking-baseline` so graders
can retrieve it. To reproduce it without changing your current checkout:

```bash
git fetch origin --tags
git worktree add --detach ../dsan6700-blocking blocking-baseline
cd ../dsan6700-blocking
uv sync --extra dev --frozen
uv run python scripts/train_model.py
INFERENCE_DELAY_SECONDS=2 \
uv run uvicorn dsan6700_ml_service.api:app --workers 1
```

Stop the other server first so port 8000 is available. Run the same
benchmark from a second terminal in that checkout, using `--label blocking`
and `--output benchmarks/blocking.json`. Restart the appropriate server
before measuring a different version. Use `INFERENCE_DELAY_SECONDS=0`
for normal operation.

## Remaining Homework 2 Work

The model integration and local concurrency audit are implemented.
Remaining team work includes:

- Strict configuration validation and startup-failure tests.
- Strict prediction-input validation.
- Docker/Compose packaging, Jetstream2 deployment and recovery checks,
  image/build/disk measurements, and deployment instructions.
- GitHub issue templates and the remaining team review records.

Deployment instructions will be added after packaging and cloud validation.
The audit branch must be reviewed and merged, and its baseline tag pushed,
before the final submission.
