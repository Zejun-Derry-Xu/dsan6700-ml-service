# DSAN 6700 ML Service

A FastAPI classification service built for DSAN 6700 by Peipei Ji,
Shuchen Liu, and Zejun Xu. Homework 2 continues the project from Homework 1
in the same repository.

## Current Features

- Installable Python package and locked dependencies managed with `uv`.
- Environment configuration with Pydantic Settings that fails fast at
  startup on invalid values.
- A trained Iris classifier: `StandardScaler` and `LogisticRegression`.
- Model loading once per application startup and reuse across requests.
- `GET /health` and `POST /predict` endpoints, with validated prediction
  input.
- API tests using an injected fake model client.
- A measured concurrency audit and a health responsiveness regression test.
- A Docker image and a Compose stack for the Jetstream2 instance.
- Ruff, Mypy, Pytest, pre-commit, and GitHub Actions.

## Project Structure

```text
.
├── .dockerignore
├── .env.development.example
├── .env.production.example
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── Dockerfile
├── compose.yml
├── pyproject.toml
├── uv.lock
├── README.md
├── scripts/
│   ├── train_model.py
│   ├── benchmark_concurrency.py
│   └── measure_docker.sh
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
    ├── test_config_startup.py
    ├── test_responsiveness.py
    └── test_schemas.py
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
example values only. Validators reject an unsupported `APP_ENV` or
`LOG_LEVEL`, a blank `APP_NAME` or `MODEL_PATH`, and a negative or
non-finite `INFERENCE_DELAY_SECONDS`. Any invalid value stops the
application during startup instead of when the first request arrives.

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

Each measurement must be a finite number greater than zero; integers and
floats are both accepted, and there is no upper limit. Missing fields,
zero or negative values, nonnumeric strings, and unexpected or misspelled
fields are rejected with HTTP 422. For example:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":0,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

The response lists each problem with its field and reason, here
`greater_than` for `sepal_length`. The field descriptions and limits also
appear in the interactive documentation at `/docs`.

## Quality Checks and Tests

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest
uv run pre-commit run --all-files
```

The tests cover:

- `test_api.py`: the `/health` response, and `/predict` passing
  measurements to an injected fake client and returning its result, even
  when `MODEL_PATH` points to a missing file.
- `test_config.py`: accepted and rejected values for every setting.
- `test_config_startup.py`: invalid environment settings prevent startup;
  valid settings start the application with a fake client.
- `test_responsiveness.py`: `/health` responds while an injected slow
  prediction remains pending.
- `test_schemas.py`: accepted measurements, feature order, and rejection of
  missing, zero, negative, nonnumeric, NaN, infinite, and unexpected
  input.

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
The blocking version is preserved under the `blocking-baseline` Git tag.
To reproduce it without changing your current checkout:

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

## Docker and Compose

Install Docker Engine with the Compose plugin on Linux, or start Docker
Desktop on macOS. Run the following commands from the repository root.
To deploy on a Jetstream2 instance, follow
[Deploy on Jetstream2](#deploy-on-jetstream2) instead.

```bash
docker compose config --quiet
docker compose up -d
```

On a fresh clone with no service image, Compose builds the image before
starting the service. The image installs locked runtime dependencies and
trains the Iris model during the build. Local Python, a local virtual
environment, and a pre-existing model artifact are not needed.

After changing source code, explicitly rebuild:

```bash
docker compose up -d --build
```

Inspect startup and health:

```bash
docker compose ps
docker compose logs --tail 50 api
curl -sS http://127.0.0.1:8000/health
curl -sS -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
docker compose exec api id
```

Expected responses are `{"status":"healthy"}` and
`{"class_id":0,"class_name":"setosa"}`. The container runs as user `app`
with UID 10001. Health may initially show `starting` before becoming
`healthy`. Port 8000 must be available; stop any local Uvicorn or old
standalone API container using that port first.

Compose passes APP_ENV, LOG_LEVEL, MODEL_PATH, and INFERENCE_DELAY_SECONDS
at runtime, with defaults of production, INFO, artifacts/iris.joblib, and
0. Values can be supplied through the shell or a local `.env` file;
shell values take precedence for Compose interpolation. For example:

```bash
INFERENCE_DELAY_SECONDS=2 docker compose up -d
```

Real `.env` files are excluded from both Git and the Docker build context.
Compose reads the file on the host and passes the listed variables into
the container; the file itself is not copied into the image. Keep
MODEL_PATH at its default unless the selected artifact exists inside the
container. Return INFERENCE_DELAY_SECONDS to 0 for normal operation.

The stack has one API service, no external dependencies, and no mutable
application data requiring a volume. The model is included in the image.
The Dockerfile provides a health check; Compose sets
`restart: unless-stopped`. An unhealthy status alone does not restart a
running container; the policy applies to process exits and Docker restarts.

Stop or remove the Compose containers with:

```bash
docker compose stop
docker compose down
```

These commands retain the built image. See [discussion.md](discussion.md)
for measured image size, cached and uncached rebuild times, and Docker
disk usage.

## Deploy on Jetstream2

These steps start the stack on a Jetstream2 Ubuntu instance from a fresh
clone. `docker compose up -d` is the whole start procedure; no Python,
virtual environment, or model artifact is needed on the instance.

### 1. Open the Port

In Exosphere or Horizon, make sure the instance's security group allows
inbound TCP traffic on port 8000. If `sudo ufw status` reports that the
firewall is active on the instance, also run `sudo ufw allow 8000/tcp`.

### 2. Install Docker on the Instance

Connect to the instance (Exosphere instances use the `exouser` account):

```bash
ssh exouser@<INSTANCE_IP>
```

Check whether Docker Engine and the Compose plugin are already installed:

```bash
docker --version
docker compose version
```

If either command fails, install Docker Engine with Docker's convenience
script, let your user run Docker, and log in again:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker "$USER"
exit
```

After reconnecting, make sure the Docker daemon starts when the instance
boots, which is what brings the stack back after an unshelve:

```bash
sudo systemctl enable --now docker
```

### 3. Clone and Start the Stack

```bash
git clone https://github.com/Zejun-Derry-Xu/dsan6700-ml-service.git
cd dsan6700-ml-service
docker compose up -d
docker compose ps
```

The first start builds the image, which trains the model, so it takes
longer than later starts. Wait until `docker compose ps` shows the `api`
service as `healthy`.

### 4. Call Every Endpoint from Outside the Instance

Run these on your own computer, not on the instance:

```bash
export INSTANCE_IP=<INSTANCE_IP>

curl -sS "http://$INSTANCE_IP:8000/health"

curl -sS -X POST "http://$INSTANCE_IP:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

curl -sS -X POST "http://$INSTANCE_IP:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":-1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

Expected responses are `{"status":"healthy"}`,
`{"class_id":0,"class_name":"setosa"}`, and an HTTP 422 validation error
for the negative measurement. The interactive documentation is at
`http://<INSTANCE_IP>:8000/docs`.

### 5. Check Recovery After an Unshelve

Shelve the instance in Exosphere, unshelve it, and wait for it to become
ready. Without logging in or running any command on the instance, repeat
the `/health` request from step 4. The Docker daemon starts at boot and
`restart: unless-stopped` restarts the container, so the service returns
on its own. A container stopped with `docker compose stop` or `down` is
not restarted.

### 6. Measure the Image and Rebuilds

On the instance, from a clean checkout, run:

```bash
bash scripts/measure_docker.sh 2>&1 | tee docker-measurements.txt
```

The script reports the image size, the rebuild time after a one-line code
change with and without the cached dependency layer, and
`docker system df` after the stack is up. It temporarily appends a comment
to `src/dsan6700_ml_service/__init__.py` and restores it before starting
the stack from the committed source. The recorded results are in
[discussion.md](discussion.md).
