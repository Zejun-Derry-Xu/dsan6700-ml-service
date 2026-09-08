# DSAN 6700 ML Service

**A minimal FastAPI project created for DSAN 6700 Homework 1 by Peipei Ji, Shuchen Liu, Zejun Xu.**


# HW1 Scope

The purpose of this project is to build a reproducible Python web service workflow, including project setup, dependency management, environment configuration, testing, code-quality checks, and continuous integration.

The project currently includes:

* Python package structure
* dependency management with `uv`
* environment configuration with Pydantic Settings
* FastAPI service
* `/health` endpoint
* Ruff, Mypy, Pytest, and pre-commit
* GitHub Actions continuous integration

The project does not currently include a trained machine-learning model or `/predict` endpoint.

# Project Structure

```text
.
├── .env.development.example
├── .env.production.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── uv.lock
├── src/
│   └── dsan6700_ml_service/
│       ├── api.py
│       └── config.py
└── tests/
    ├── test_api.py
    └── test_config.py
```


# How to Reproduce and Run the Project

The steps below explain how to set up the project on a new computer.

All commands shown in code blocks should be **copied into a Terminal window and executed by pressing Enter**.

## Step 1 — Check the Required Tools

This project requires:

* Python 3.12 or later
* `uv`
* Git

Open Terminal and run:

```bash
python --version
uv --version
git --version
```

These commands check whether Python, `uv`, and Git are available on your computer.

## Step 2 — Download the Project from GitHub

In Terminal, copy and run:

```bash
git clone https://github.com/Zejun-Derry-Xu/dsan6700-ml-service.git
```

This downloads the repository to your computer.

Then enter the project folder:

```bash
cd dsan6700-ml-service
```

The remaining commands should be run from inside this folder.

## Step 3 — Install the Project Dependencies

Run:

```bash
uv sync --extra dev --frozen
```

This installs the packages required to run and check the project.

The command uses the committed `uv.lock` file so that team members and GitHub Actions use the same resolved dependency versions.

Then install the pre-commit hooks:

```bash
uv run pre-commit install
```

## Step 4 — Set the Environment Configuration

Application settings are defined in:

```text
src/dsan6700_ml_service/config.py
```

The project currently uses three environment variables:

| Variable    | Purpose                                                        |
| ----------- | -------------------------------------------------------------- |
| `APP_NAME`  | Application name                                               |
| `APP_ENV`   | Current environment: `development`, `testing`, or `production` |
| `LOG_LEVEL` | Logging level such as `DEBUG` or `INFO`                        |

The repository includes two example configuration files:

```text
.env.development.example
.env.production.example
```

These are **example templates** showing what the configuration should look like. They do not contain private information and are not automatically loaded by the current application.

For local development on macOS or Linux, copy the following commands into Terminal:

```bash
export APP_NAME="DSAN 6700 ML Service"
export APP_ENV="development"
export LOG_LEVEL="DEBUG"
```

If these variables are not set, the default values defined in `Settings` are used.

Invalid configuration values are rejected by Pydantic Settings.

For example, `APP_ENV` must be one of:

```text
development
testing
production
```

**Do not upload private configuration to GitHub**, including:

* passwords
* API tokens
* private keys
* database credentials
* real `.env` files containing sensitive values

The `.env.development.example` and `.env.production.example` files should contain example values only.

## Step 5 — Start the FastAPI Service

In Terminal, run:

```bash
uv run uvicorn dsan6700_ml_service.api:app --reload
```

This starts the FastAPI application on your computer.

If the server starts successfully, it will normally be available at:

```text
http://127.0.0.1:8000
```

Keep this Terminal window open while the server is running.

To stop the server later, press:

```text
Ctrl + C
```

## Step 6 — Check the Health Endpoint

While the FastAPI server is still running, open a **second Terminal window**.

Run:

```bash
curl http://127.0.0.1:8000/health
```

You should receive:

```json
{"status":"healthy"}
```

This means the FastAPI service is running and responding correctly.

The `/health` endpoint only checks whether the service is working. It does not perform machine-learning prediction.

## Step 7 — Run the Project Checks

The following commands check different parts of the project.

Run them from the project folder in Terminal.

### Check code quality with Ruff

```bash
uv run ruff check src/ tests/
```

### Check code formatting with Ruff

```bash
uv run ruff format --check src/ tests/
```

### Check Python types with Mypy

```bash
uv run mypy src/
```

### Run automated tests with Pytest

```bash
uv run pytest
```

The current tests check:

* whether `/health` returns HTTP `200` and `{"status": "healthy"}`
* whether an invalid `APP_ENV` value is rejected

### Run all pre-commit checks

```bash
uv run pre-commit run --all-files
```

These checks help catch code-quality, formatting, type, and testing problems before changes are submitted.


# Continuous Integration

The repository also includes a GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

Whenever code is pushed to GitHub or a Pull Request is created, GitHub automatically creates a clean environment and runs:

```bash
uv sync --extra dev --frozen
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest
```

This checks that the project works outside an individual team member's computer.

A green GitHub Actions result means all configured CI checks passed.
