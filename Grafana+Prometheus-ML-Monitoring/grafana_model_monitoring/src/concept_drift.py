from sklearn.metrics import accuracy_score



def detect_concept_drift(
    model,
    X_reference,
    y_reference,
    X_current,
    y_current,
    threshold: float = 0.10,
):
    reference_predictions = model.predict(X_reference)
    current_predictions = model.predict(X_current)
    reference_accuracy = accuracy_score(y_reference, reference_predictions)
    current_accuracy = accuracy_score(y_current, current_predictions)
    relative_performance_drop = max(reference_accuracy - current_accuracy, 0.0)
    is_drift = relative_performance_drop > threshold
    return is_drift, relative_performance_drop
