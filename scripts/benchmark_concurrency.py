"""Measure ten concurrent prediction requests."""

import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter

import httpx

PAYLOAD = {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2,
}


async def measure(label: str) -> dict[str, object]:
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000",
        timeout=60.0,
        limits=httpx.Limits(max_connections=10),
    ) as client:
        # Check the server and model before starting the measurement.
        warmup = await client.post("/predict", json=PAYLOAD)
        warmup.raise_for_status()
        assert warmup.json()["class_name"] == "setosa"

        async def send_one(number: int) -> dict[str, object]:
            started = perf_counter()
            response = await client.post("/predict", json=PAYLOAD)
            elapsed = perf_counter() - started
            response.raise_for_status()
            prediction = response.json()
            assert prediction["class_name"] == "setosa"
            return {
                "request": number,
                "seconds": round(elapsed, 4),
                "prediction": prediction,
            }

        started = perf_counter()
        results = await asyncio.gather(*(send_one(number) for number in range(1, 11)))
        total = perf_counter() - started

    return {
        "label": label,
        "request_count": 10,
        "total_seconds": round(total, 4),
        "slowest_request_seconds": max(float(item["seconds"]) for item in results),
        "requests": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = asyncio.run(measure(args.label))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, indent=2)
    args.output.write_text(content + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
