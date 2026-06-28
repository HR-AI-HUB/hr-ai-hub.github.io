import pandas as pd



def detect_data_drift(reference_data: pd.DataFrame, current_data: pd.DataFrame, threshold: float = 0.12):
    drift_scores = {}
    for column in reference_data.columns:
        reference_mean = reference_data[column].mean()
        current_mean = current_data[column].mean()
        reference_std = reference_data[column].std() or 1.0
        drift_scores[column] = abs(current_mean - reference_mean) / reference_std

    overall_drift_score = sum(drift_scores.values()) / len(drift_scores)
    is_drift = overall_drift_score > threshold
    return is_drift, drift_scores, overall_drift_score
