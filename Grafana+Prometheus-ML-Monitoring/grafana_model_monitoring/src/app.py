from pathlib import Path
from threading import Thread
from time import sleep
import sys

import joblib
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from sklearn.datasets import make_classification
from werkzeug.serving import make_server

project_dir = Path(__file__).resolve().parent.parent
src_dir = project_dir / "src"
models_dir = project_dir / "models"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from concept_drift import detect_concept_drift
from data_drift import detect_data_drift

model_path = models_dir / "tutorial_model.joblib"
reference_data_path = models_dir / "reference_data.joblib"
model = joblib.load(model_path)
reference_data = joblib.load(reference_data_path)
feature_columns = list(reference_data.columns)

app = Flask("grafana_prometheus_tutorial")
tutorial_registry = CollectorRegistry()

prediction_counter = Counter(
    "tutorial_predictions_total",
    "Total number of tutorial prediction requests",
    labelnames=["prediction_class", "status"],
    registry=tutorial_registry,
)
prediction_latency = Histogram(
    "tutorial_prediction_latency_seconds",
    "Latency of tutorial prediction requests",
    registry=tutorial_registry,
)
prediction_confidence_counter = Counter(
    "tutorial_prediction_confidence_total",
    "Predictions grouped by confidence band",
    labelnames=["confidence_band"],
    registry=tutorial_registry,
)
last_prediction = Gauge(
    "tutorial_last_prediction",
    "Latest prediction value returned by the tutorial app",
    registry=tutorial_registry,
)
last_prediction_confidence = Gauge(
    "tutorial_last_prediction_confidence",
    "Latest prediction confidence score returned by the tutorial app",
    registry=tutorial_registry,
)
data_drift_gauge = Gauge(
    "tutorial_data_drift_score",
    "Average feature drift score against the reference dataset",
    registry=tutorial_registry,
)
concept_drift_gauge = Gauge(
    "tutorial_concept_drift_score",
    "Relative performance drop between reference and current batches",
    registry=tutorial_registry,
)

def classify_prediction(score):
    return "positive" if score >= 0.5 else "negative"

def confidence_band(confidence):
    if confidence < 0.4:
        return "low"
    if confidence < 0.75:
        return "medium"
    return "high"

def build_current_batch(sample_size=200):
    X_current, y_current = make_classification(
        n_samples=sample_size,
        n_features=len(feature_columns),
        n_informative=4,
        n_redundant=0,
        random_state=None,
        class_sep=0.9,
        flip_y=0.08,
    )
    current_df = pd.DataFrame(X_current, columns=feature_columns)
    return current_df, y_current

def update_drift_metrics(current_df=None, y_current=None):
    if current_df is None or y_current is None:
        current_df, y_current = build_current_batch(sample_size=200)

    reference_sample = reference_data.sample(
        n=min(len(reference_data), len(current_df)),
        random_state=42,
    )
    is_data_drift, drift_scores, overall_drift_score = detect_data_drift(reference_sample, current_df)
    data_drift_gauge.set(float(overall_drift_score))

    X_reference = reference_sample[feature_columns]
    y_reference = model.predict(X_reference)
    is_concept_drift, concept_drift_score = detect_concept_drift(
        model,
        X_reference,
        y_reference,
        current_df[feature_columns],
        y_current,
    )
    concept_drift_gauge.set(float(concept_drift_score))

    return {
        "is_data_drift": bool(is_data_drift),
        "is_concept_drift": bool(is_concept_drift),
        "data_drift_score": round(float(overall_drift_score), 4),
        "concept_drift_score": round(float(concept_drift_score), 4),
        "feature_drift": {name: round(float(score), 4) for name, score in drift_scores.items()},
    }

@app.get("/")
def home():
    base_url = request.host_url.rstrip("/")
    return jsonify({
        "message": "Grafana/Prometheus tutorial app is running",
        "metrics": f"{base_url}/metrics",
        "predict": f"{base_url}/predict",
        "model_path": str(model_path),
    })

@app.get("/predict")
def predict():
    with prediction_latency.time():
        current_df, _ = build_current_batch(sample_size=1)
        probability = float(model.predict_proba(current_df)[0][1])
        prediction_class = classify_prediction(probability)
        confidence = float(max(probability, 1.0 - probability))
        band = confidence_band(confidence)
        status = "success"

        prediction_counter.labels(prediction_class=prediction_class, status=status).inc()
        prediction_confidence_counter.labels(confidence_band=band).inc()
        last_prediction.set(probability)
        last_prediction_confidence.set(confidence)

        drift_summary = update_drift_metrics()

        return jsonify({
            "prediction_score": round(probability, 4),
            "prediction_class": prediction_class,
            "confidence": round(confidence, 4),
            "confidence_band": band,
            "status": status,
            "data_drift_score": drift_summary["data_drift_score"],
            "concept_drift_score": drift_summary["concept_drift_score"],
            "is_data_drift": drift_summary["is_data_drift"],
            "is_concept_drift": drift_summary["is_concept_drift"],
        })

@app.get("/metrics")
def metrics():
    return generate_latest(tutorial_registry), 200, {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}

class ServerThread(Thread):
    def __init__(self, flask_app, host="0.0.0.0", port=8000):
        super().__init__(daemon=True)
        self.server = make_server(host, port, flask_app)
        self.context = flask_app.app_context()
        self.context.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_drift_metrics, "interval", seconds=15, id="drift_refresh", replace_existing=True)
    scheduler.start()
    update_drift_metrics()

    server_thread = ServerThread(app)
    server_thread.start()
    print("Tutorial app started.")
    print("Open http://localhost:8000/")
    print("Open http://localhost:8000/metrics")
    print("Call http://localhost:8000/predict a few times to generate metrics.")

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
        server_thread.shutdown()
