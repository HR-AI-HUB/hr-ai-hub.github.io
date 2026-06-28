from pathlib import Path

import joblib
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split



FEATURE_COLUMNS = [f"feature_{index}" for index in range(6)]



def build_reference_dataframe(X):
    return pd.DataFrame(X, columns=FEATURE_COLUMNS)



def train_and_save_model(model_path: Path, reference_data_path: Path):
    X, y = make_classification(
        n_samples=1000,
        n_features=6,
        n_informative=4,
        n_redundant=0,
        random_state=42,
        class_sep=1.2,
    )
    X_df = build_reference_dataframe(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y, test_size=0.2, random_state=42
    )
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    reference_data_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(X_train.reset_index(drop=True), reference_data_path)
    return {
        "accuracy": score,
        "model_path": str(model_path),
        "reference_data_path": str(reference_data_path),
    }



if __name__ == "__main__":
    models_dir = Path.cwd() / "models"
    result = train_and_save_model(
        models_dir / "tutorial_model.joblib",
        models_dir / "reference_data.joblib",
    )
    print(result)
