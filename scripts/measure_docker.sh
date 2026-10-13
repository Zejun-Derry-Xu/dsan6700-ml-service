#!/usr/bin/env bash
# Build, start, and measure the Compose stack on the current host.
#
# Run from a clean checkout on the Jetstream2 instance:
#   bash scripts/measure_docker.sh 2>&1 | tee docker-measurements.txt
#
# The script temporarily appends one comment line to a source file to time
# rebuilds after a one-line code change, then restores the file and starts
# the stack from the committed source.

set -euo pipefail

cd "$(dirname "$0")/.."

CHANGED_FILE="src/dsan6700_ml_service/__init__.py"
IMAGE="dsan6700-ml-service:local"

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree is not clean; commit or stash changes first." >&2
    exit 1
fi

restore() {
    git checkout -- "$CHANGED_FILE"
}
trap restore EXIT

timed() {
    local label="$1"
    shift
    local started ended
    started=$(date +%s.%N)
    "$@" >/dev/null
    ended=$(date +%s.%N)
    awk -v label="$label" -v a="$started" -v b="$ended" \
        'BEGIN { printf "%s: %.2f seconds\n", label, b - a }'
}

section() {
    printf '\n== %s\n' "$1"
}

section "Environment"
echo "Commit: $(git rev-parse --short HEAD)"
echo "Host: $(uname -srm)"
docker version --format 'Docker Engine: {{.Server.Version}}'
docker compose version

section "Initial build"
timed "Initial build" docker compose build api

section "Rebuild after a one-line code change"
echo "# Rebuild timing marker." >>"$CHANGED_FILE"
timed "Rebuild with cached dependency layer" docker compose build api
timed "Rebuild without cache (--no-cache)" docker compose build --no-cache api

restore
trap - EXIT

section "Rebuild from committed source and start the stack"
docker compose up -d --build

container=$(docker compose ps -q api)
status="starting"
for _ in $(seq 1 60); do
    status=$(docker inspect --format '{{.State.Health.Status}}' "$container")
    [[ "$status" == "healthy" ]] && break
    sleep 2
done
echo "Container health: $status"

section "Requests from the instance"
curl -sS http://127.0.0.1:8000/health
echo
curl -sS -X POST http://127.0.0.1:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
echo
echo "Container user: $(docker compose exec -T api id)"

section "Compose services"
docker compose ps

section "Image size"
docker image ls "$IMAGE"
docker image inspect --format 'Image content size: {{.Size}} bytes' "$IMAGE"

section "docker system df"
docker system df
