# DSAN 6700 ML Service

This is a minimal Python web-service framework created for **DSAN 6700 Homework 1** by Shuchen Liu, Zejun Xu, Peipei Ji.

## Homework 1 Scope
HW1 focuses on building a reproducible software-engineering framework around a Python service, including:

- Python package structure
- dependency and environment management
- typed configuration
- FastAPI service startup
- automated testing
- linting, formatting, and type checking
- pre-commit checks
- GitHub Actions continuous integration
- team collaboration and documentation

The repository currently contains a working FastAPI service with a typed `GET /health` endpoint. It does not contain a trained machine-learning model or prediction functionality. In other words, HW1 builds the software framework and validation pipeline that a future ML application could use.


## Project Structure

```text
.
├── .env.development.example
├── .env.production.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── .python-version
├── pyproject.toml
├── README.md
├── uv.lock
├── src/
│   └── dsan6700_ml_service/
│       ├── __init__.py
│       ├── api.py
│       └── config.py
└── tests/
    ├── test_api.py
    └── test_config.py
```

Main responsibilities of these files:

- `pyproject.toml` defines the package, Python requirement, dependencies, build system, and tool configuration.
- `uv.lock` records the resolved dependency versions for reproducible installation.
- `api.py` defines the FastAPI application and health endpoint.
- `config.py` defines typed application settings using Pydantic Settings.
- `tests/` contains automated behavior and configuration tests.
- `.pre-commit-config.yaml` defines checks that can run before commits.
- `.github/workflows/ci.yml` defines the automated GitHub Actions validation workflow.
- `README.md` explains how another developer can reproduce, run, and check the project.

---
## Reproduce and Run the Project from Scratch

The steps below follow the order a new developer would use to reproduce the project on another computer.

### Step 1 — Prepare Python 3.12 and `uv`

This project uses **Python 3.12** in continuous integration and requires Python `>=3.12`.

It also uses **`uv`** to manage the Python environment and project dependencies.

Check that both are available:

```bash
python --version
uv --version
```

Why they are needed:

- **Python 3.12** provides the runtime used to execute the project.
- **`uv`** creates the project environment and installs the dependencies defined by `pyproject.toml` and `uv.lock`.

---

### Step 2 — Clone the Repository

Clone the GitHub repository and enter the project directory:

```bash
git clone https://github.com/Zejun-Derry-Xu/dsan6700-ml-service.git
cd dsan6700-ml-service
```

Cloning creates a local copy of the project, including its source code, configuration files, tests, dependency lockfile, and Git history.

---

### Step 3 — Install the Project and Dependencies

Install the runtime and development dependencies using the committed lockfile:

```bash
uv sync --extra dev --frozen
```

This command has three important parts:

- `uv sync` creates or updates the project environment and installs its dependencies.
- `--extra dev` also installs development tools such as Ruff, Mypy, Pytest, and pre-commit.
- `--frozen` requires the installation to follow the existing `uv.lock` instead of changing dependency versions.

Using the lockfile helps the team and GitHub Actions work with the same resolved dependency versions.

Install the Git pre-commit hooks after the dependencies are available:

```bash
uv run pre-commit install
```

---

### Step 4 — Understand and Set the Environment Configuration

Application settings are defined in:

```text
src/dsan6700_ml_service/config.py
```

The project currently supports three settings:

| Environment variable | Purpose | Allowed values / default |
| --- | --- | --- |
| `APP_NAME` | Name of the application | Default: `DSAN 6700 ML Service` |
| `APP_ENV` | Current application environment | `development`, `testing`, or `production`; default: `development` |
| `LOG_LEVEL` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`; default: `INFO` |

Two example configuration files are included:

```text
.env.development.example
.env.production.example
```

These files are **templates** showing which environment variables the project expects and what development or production values may look like. They do not contain real secrets.

For example, `.env.development.example` contains development-style values, while `.env.production.example` contains production-style values.

The current `Settings` class reads values from the **process environment**. The example files are therefore references; they are not automatically loaded by the application.

To set the development values manually on macOS or Linux, run:

```bash
export APP_NAME="DSAN 6700 ML Service"
export APP_ENV="development"
export LOG_LEVEL="DEBUG"
```

If no environment variables are provided, the defaults in `Settings` are used.

Pydantic validates the settings when `Settings` is created. For example, an unsupported value such as:

```text
APP_ENV=banana
```

is rejected because `APP_ENV` only accepts `development`, `testing`, or `production`.

#### Do not commit secrets

Do not commit real private configuration to the repository, including:

- passwords
- API tokens
- SSH private keys
- database credentials
- real `.env` files containing sensitive values

The committed `.env.development.example` and `.env.production.example` files should contain only safe example values.

---

### Step 5 — Start the FastAPI Service

Start the local development server with Uvicorn:

```bash
uv run uvicorn dsan6700_ml_service.api:app --reload
```

Here:

- **FastAPI** defines the web application and its endpoints.
- **Uvicorn** runs the application as a local web server and listens for HTTP requests.
- `--reload` restarts the development server automatically when Python source files change.

The service should be available at:

```text
http://127.0.0.1:8000
```

Stop the server with `Ctrl+C`.

---

### Step 6 — Check the Health Endpoint

The current API exposes one endpoint:

```text
GET /health
```

With the FastAPI server running, open another terminal and run:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

A successful request returns HTTP status `200`.

The health endpoint is intentionally simple. Its purpose is to confirm that the web service can start and respond correctly; it does not perform machine-learning prediction.

---

### Step 7 — Run Tests and Code-Quality Checks

Before committing changes, run the project checks locally.

#### Ruff lint

```bash
uv run ruff check src/ tests/
```

Ruff lint checks the Python source and tests for common errors and rule violations.

#### Ruff format check

```bash
uv run ruff format --check src/ tests/
```

This checks whether the Python files follow the project's formatting rules without modifying them.

#### Mypy

```bash
uv run mypy src/
```

Mypy checks whether the Python type hints are internally consistent.

#### Pytest

```bash
uv run pytest
```

The current tests verify that:

- `GET /health` returns HTTP `200` and `{"status": "healthy"}`.
- an invalid `APP_ENV` value is rejected by the `Settings` model.

#### pre-commit

Run all configured pre-commit hooks manually with:

```bash
uv run pre-commit run --all-files
```

The pre-commit configuration runs Ruff checks and formatting and also performs basic repository checks such as YAML validation, large-file detection, private-key detection, end-of-file fixing, and trailing-whitespace cleanup.

Together, these tools check different parts of the project:

- **Ruff** checks code quality and formatting.
- **Mypy** checks type consistency.
- **Pytest** checks actual program behavior.
- **pre-commit** runs selected checks before changes are committed to Git history.

---

## Continuous Integration with GitHub Actions

The repository includes:

```text
.github/workflows/ci.yml
```

GitHub Actions automatically runs the CI workflow on both:

- `push`
- `pull_request`

The workflow creates a clean Ubuntu runner, sets up Python 3.12 and `uv`, installs the project from the frozen lockfile, and then runs:

```bash
uv sync --extra dev --frozen
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest
```

This provides an independent check that the project can be installed and validated outside an individual team member's local computer.

A green GitHub Actions run means all checks in the workflow completed successfully.
