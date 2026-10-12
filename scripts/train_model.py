"""Train and save an Iris classification model."""

import argparse
from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/iris.joblib"),
    )
    args = parser.parse_args()

    iris = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        iris.data,
        iris.target,
        test_size=0.2,
        random_state=42,
        stratify=iris.target,
    )

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=42),
    )
    model.fit(x_train, y_train)

    accuracy = model.score(x_test, y_test)

    artifact = {
        "format_version": 1,
        "model": model,
        "class_names": iris.target_names.tolist(),
        "feature_names": FEATURE_NAMES,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.output)

    saved_artifact = joblib.load(args.output)
    sample = [[5.1, 3.5, 1.4, 0.2]]
    class_id = int(saved_artifact["model"].predict(sample)[0])
    class_name = saved_artifact["class_names"][class_id]

    print(f"Training samples: {len(x_train)}")
    print(f"Test samples: {len(x_test)}")
    print(f"Test accuracy: {accuracy:.3f}")
    print(f"Saved model: {args.output}")
    print(f"Reloaded model prediction: {class_id} ({class_name})")


if __name__ == "__main__":
    main()
