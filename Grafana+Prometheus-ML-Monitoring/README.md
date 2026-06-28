# Grafana + Prometheus ML Monitoring

This project adapts the DataCamp tutorial on monitoring machine learning models with Grafana and Prometheus for a Windows 11 workflow and a notebook-first development style.

Source tutorial:
- https://www.datacamp.com/tutorial/grafana-tutorial-monitoring-machine-learning-models

## Project Tree

This repository map is included for the project root at [./grafana_model_monitoring](D:/OneDrive%20-%20Hogeschool%20Rotterdam/1_CURRENT_DOCUMENTS/DATALAB_ALIGNMENT/PROMETHEUS+GRAFANA/grafana_model_monitoring).

```text
grafana_model_monitoring/
|-- .dockerignore
|-- dashboards/
|   `-- grafana-prometheus-ml-monitoring.json
|-- docker-compose.yml
|-- Dockerfile
|-- grafana/
|   `-- provisioning/
|       |-- dashboards/
|       |   `-- dashboard-provider.yml
|       `-- datasources/
|           `-- prometheus.yml
|-- Grafana-Prometheus_TEST_V001.ipynb
|-- Grafana-Prometheus_TEST_V001 - Copy.ipynb
|-- models/
|   |-- reference_data.joblib
|   `-- tutorial_model.joblib
|-- prometheus.docker.yml
|-- prometheus.yml
|-- README-GRAFANA-PROMETHEUS.md
|-- requirements.txt
`-- src/
	|-- app.py
	|-- concept_drift.py
	|-- data_drift.py
	`-- train.py
```

Component overview:
- `Grafana-Prometheus_TEST_V001.ipynb` is the notebook-first tutorial workflow for Windows 11.
- `src/` contains the runnable Python source generated and used by the notebook.
- `models/` stores the trained model and reference dataset used by the monitoring app.
- `prometheus.yml` and `prometheus.docker.yml` separate Windows-hosted and Docker-hosted scrape modes.
- `dashboards/` stores the exported Grafana dashboard JSON.
- `grafana/provisioning/` contains automatic datasource and dashboard provisioning for Docker Compose mode.
- `docker-compose.yml` and `Dockerfile` define the containerized local stack.

## What Was Built

The final setup contains:
- A trained tutorial model saved to `models/tutorial_model.joblib`
- Reference data saved to `models/reference_data.joblib`
- A Flask monitoring app in `src/app.py`
- Drift helpers in `src/data_drift.py` and `src/concept_drift.py`
- Prometheus scrape configs for both Windows-hosted and Docker-hosted modes
- A Grafana dashboard backed by Prometheus

The dashboard now shows these working panels:
- Predictions by Class
- Confidence Bands
- Average Prediction Latency
- Last Prediction
- Data Drift Score
- Concept Drift Score

## How The Dashboard Was Built

The DataCamp tutorial was used as the conceptual base, but the implementation was adjusted to fit this project and the Windows environment.

Main adaptations:
- The tutorial was implemented as a Jupyter notebook first, then mirrored into reusable Python files under `src/`
- The app exposes Prometheus metrics from a dedicated `CollectorRegistry()` so notebook reruns do not create duplicate metric registration errors
- The model is a scikit-learn classifier trained from generated data and saved with `joblib`
- The app computes both prediction metrics and simple data/concept drift metrics
- A background scheduler refreshes drift metrics every 15 seconds
- The Flask app binds to `0.0.0.0` so it works correctly inside Docker

The live dashboard in Grafana was created against the Prometheus data source and uses these stable PromQL queries:

```promql
sum by (prediction_class) (tutorial_predictions_total{status="success"})
```

```promql
sum by (confidence_band) (tutorial_prediction_confidence_total)
```

```promql
rate(tutorial_prediction_latency_seconds_sum[$__rate_interval]) / rate(tutorial_prediction_latency_seconds_count[$__rate_interval])
```

```promql
tutorial_last_prediction
```

```promql
tutorial_data_drift_score
```

```promql
tutorial_concept_drift_score
```

## Windows 11 Notebook Workflow

The notebook was created to run on a Windows 11 PC in VS Code with a Conda environment.

Environment used:
- Conda environment: `grafana_tutorial`
- Python: `3.8`
- Notebook kernel: `Python (grafana_tutorial)`

Typical setup flow:

```powershell
conda create -n grafana_tutorial python=3.8 -y
conda activate grafana_tutorial
```

Project dependencies were installed from `requirements.txt`.

For Jupyter support on Windows, the environment also needed:
- `ipykernel`
- `jupyter`
- `notebook`
- `pywinpty`

The kernel was then registered for VS Code.

Important Windows-specific adjustments:
- Bash commands such as `touch src/{app.py,...}` do not work in PowerShell, so file creation was done in Python instead
- The notebook setup cell was made idempotent so rerunning it does not fail if `src/` or the generated files already exist
- Docker networking required different Prometheus targets depending on whether the app ran on Windows or inside Docker

## Notebook Structure

The notebook `Grafana-Prometheus_TEST_V001.ipynb` was built in stages:
- Environment and file setup
- Training code generation and model artifact creation
- Drift helper generation
- Flask monitoring app generation and execution
- Traffic generation to create metrics
- Prometheus configuration guidance
- Grafana data source and dashboard guidance
- Docker Compose guidance for the full stack

The notebook also writes the runnable source files so the notebook is not the only source of truth.

## Runtime Modes

Two Prometheus modes are supported.

Windows-hosted app mode:
- App runs from the notebook or from `python src/app.py`
- Prometheus uses `prometheus.yml`
- Scrape target: `host.docker.internal:8000`

Docker Compose mode:
- App, Prometheus, and Grafana run together with `docker compose`
- Prometheus uses `prometheus.docker.yml`
- Scrape target: `tutorial-app:8000`

## Docker Compose Mode

The full stack can be started with:

```powershell
docker compose up --build -d
```

Services:
- App: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

The Grafana data source was configured to use:

```text
http://prometheus:9090
```

Grafana is also provisioned automatically in Docker Compose mode:
- Datasource provisioning file: `grafana/provisioning/datasources/prometheus.yml`
- Dashboard provider file: `grafana/provisioning/dashboards/dashboard-provider.yml`
- Exported dashboard JSON: `dashboards/grafana-prometheus-ml-monitoring.json`

That means a fresh `docker compose up --build -d` can recreate the Prometheus datasource and load the dashboard without manual UI setup.

## Final Outcome

The Grafana dashboard was created and verified in the running Grafana instance.

Working dashboard URL:
- http://localhost:3000/d/grafana-prom-ml-monitor/grafana-prometheus-ml-monitoring

The dashboard is backed by live Prometheus data from the tutorial app and reflects generated prediction traffic plus drift metrics.

## Reusable Dashboard Export

The working dashboard has also been exported to:
- `dashboards/grafana-prometheus-ml-monitoring.json`

This file is set up for the provisioned Docker Compose datasource named `Prometheus`.

That makes the dashboard easier to version in Git and recreate in the local stack without rebuilding it manually in the UI. If you import it into a different Grafana instance, point the panels at the target Prometheus datasource if the datasource name differs.