import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression


def train_or_create_classifier():
    os.makedirs("api/meta_model_artifacts", exist_ok=True)
    categories = ["gan", "diffusion", "real"]

    np.random.seed(42)
    dim = 768
    X_gan = np.random.randn(100, dim) + 0.8
    X_diff = np.random.randn(100, dim) - 0.8
    X_real = np.random.randn(100, dim)

    X = np.vstack([X_gan, X_diff, X_real])
    y = np.array([0] * 100 + [1] * 100 + [2] * 100)

    clf = LogisticRegression(max_iter=1000, C=1.0)
    clf.fit(X, y)

    clf_path = "api/meta_model_artifacts/generator_clf.joblib"
    labels_path = "api/meta_model_artifacts/generator_labels.joblib"

    joblib.dump(clf, clf_path)
    joblib.dump(categories, labels_path)
    print(f"Saved generator classifier artifact to {clf_path} and {labels_path}")


if __name__ == "__main__":
    train_or_create_classifier()
