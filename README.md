# Nextflow Workflow Events Dashboard

This project provides a web-based dashboard for visualizing Nextflow workflow events using Dash and Plotly. It integrates with a Flask server to handle POST requests containing workflow events and metadata.

## Prerequisites

- **Python 3.x**
- **pip** (`Python package manager`)

## Installation

1. **Clone the repository**:
   ```bash
   git clone ssh://git@ser4988-a.tjh.tju.edu:2224/tools/nf-weblog_dashboard.git
   cd nextflow-dashboard
   ```

2. **Install the required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Dashboard

To start the dashboard:

```bash
python app.py
```

The dashboard will be accessible at `http://<your-server-ip>:8050`.

## Sending Workflow Events

You can send workflow events to the dashboard using a POST request. Below is an example using `curl`:

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "trace": {
    "task_id": 528,
    "status": "RUNNING",
    "hash": "b0/af20a2",
    "name": "CardiacPET_pipeline:crop_image (38)",
    "exit": 2147483647,
    "submit": 1724981681642,
    "start": 1724981681739,
    "process": "CardiacPET_pipeline:crop_image",
    "container": "wookjinchoi/radiomics-tools:latest",
    "attempt": 1,
    "script": "crop_image(\".nrrd\", \"-label.nrrd\")",
    "workdir": "/home/wxc151/gitRepos/radiomics_pipelines/HeartToxicity_pipeline/work/b0/af20a267c1780f7ef473634d37dcfb",
    "cpus": 1
  },
  "runId": "64fbe891-6874-4c9d-a396-15a474abb3b3",
  "event": "process_started",
  "runName": "stupefied_bardeen",
  "utcTime": "2024-08-30T01:34:41Z"
}' http://<your-server-ip>:8050/nf-weblog
```

## Project Structure

- **`app.py`**: The main script that runs the Dash app and Flask server.`
- **`requirements.txt`**: Contains the Python packages required for the project.

## Features & Details

- **Timeline Graph**: Shows workflow tasks on a Gantt chart with color coding for different processes.
- **Event Details**: Displays details of the most recent event including run name, event type, and metadata information.


## Acknowledgements

- [Dash](https://dash.plotly.com/)
- [Flask](https://flask.palletsprojects.com/)
- [Plotly](https://plotly.com/python/)
