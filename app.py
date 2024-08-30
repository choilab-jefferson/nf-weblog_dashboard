import dash
import json
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask server
server = Flask(__name__)

# Initialize the Dash app
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Data storage
workflow_data = []
running_tasks = {}
accumulated_tasks = {}
metadata_info = {}

# Define the layout of the Dash app
app.layout = dbc.Container([
    html.H1("Nextflow Workflow Events Dashboard"),
    dcc.Graph(id="workflow-timeline"),
    html.Div(id="event-details"),
    dcc.Interval(id="interval-component", interval=1000, n_intervals=0)
])

# Convert UTC time to local time
def utc_to_local(utc_str):
    utc_time = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
    local_tz = pytz.timezone('America/New_York')  # Change this to your local timezone
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_time

def get_local_time_from_milliseconds(milliseconds):
    """Converts a UNIX timestamp in milliseconds to a local datetime string."""
    return utc_to_local(datetime.utcfromtimestamp(milliseconds / 1000.0).strftime('%Y-%m-%dT%H:%M:%SZ'))

def filter_metadata(metadata):
    """Recursively filter out 'availableZoneIds' from the metadata."""
    if isinstance(metadata, dict):
        return {
            k: filter_metadata(v)
            for k, v in metadata.items()
            if k != 'availableZoneIds'
        }
    elif isinstance(metadata, list):
        return [filter_metadata(item) for item in metadata]
    else:
        return metadata

@app.callback(Output('workflow-timeline', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph(n):
    if not workflow_data:
        return dash.no_update

    global running_tasks, accumulated_tasks, metadata_info
    completed_tasks = {}

    for data in workflow_data:
        trace = data.get('trace', {})
        metadata = data.get('metadata', {})

        # Update metadata information with metadata from completed events
        if metadata:
            metadata_info.update(filter_metadata(metadata.get('workflow', {})))

        if trace:
            task_id = trace.get('task_id')
            process = trace.get('process', 'Unknown')
            status = trace.get('status')
            timestamp = utc_to_local(data['utcTime'])
            start = trace.get('start')
            submit = trace.get('submit')
            complete = trace.get('complete')

            # Determine start time
            if start is not None and start != 0:
                start_time = get_local_time_from_milliseconds(start)
            elif submit is not None and submit != 0:
                start_time = get_local_time_from_milliseconds(submit)
            else:
                start_time = timestamp  # Use default timestamp if no start or submit time is available

            # Determine end time
            if complete is not None:
                end_time = get_local_time_from_milliseconds(complete)
            else:
                end_time = timestamp  # Use default timestamp if no complete time is available
            
            if status == 'SUBMITTED':
                # Start tracking task
                running_tasks[task_id] = {'Task ID': task_id, 'Process': process, 'Start': start_time, 'End': end_time}
            
            elif status == 'RUNNING':
                # Update running task end time to current time
                if task_id in running_tasks:
                    running_tasks[task_id]['End'] = end_time
            
            elif status == 'COMPLETED':
                # End the task and store its time
                if task_id in running_tasks:
                    task_info = running_tasks.pop(task_id)
                    task_info['End'] = end_time
                    process = task_info['Process']
                    start_time = task_info['Start']
                    
                if process not in completed_tasks:
                    completed_tasks[process] = []
                
                completed_tasks[process].append({
                    'Start': start_time,
                    'End': end_time
                })

    # Clear the workflow_data after processing
    workflow_data.clear()

    # Accumulate times for each process
    for process, tasks in completed_tasks.items():
        start_times = [task['Start'] for task in tasks]
        end_times = [task['End'] for task in tasks]
        
        # Find the overall start and end time for the process
        overall_start = min(start_times)
        overall_end = max(end_times)

        if process in accumulated_tasks:
            accumulated_tasks[process]['End'] = overall_end
        else:
            accumulated_tasks[process] = {
                'Task ID': process,
                'Process': process,
                'Start': overall_start,
                'End': overall_end
            }

    # Convert data to DataFrame
    df = pd.DataFrame(accumulated_tasks | running_tasks).T

    # Update the plot based on metadata, if available
    fig = px.timeline(df, x_start='Start', x_end='End', y='Process', color='Process',
                      title="Workflow Task Timeline",
                      labels={'Start': 'Start Time', 'End': 'End Time'},
                      category_orders={'Process': df.sort_values('Start')['Process'].unique().tolist()})

    fig.update_layout(xaxis_title='Time',
                      yaxis_title='Process')

    return fig

@app.callback(Output('event-details', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_event_details(n):
    if not workflow_data or len(workflow_data) == 0:
        return dash.no_update

    latest_event = workflow_data[-1]

    details_layout = dbc.Card([
        dbc.CardBody([
            html.H4(f"Run Name: {latest_event.get('runName', 'N/A')}", className="card-title"),
            html.H6(f"Event: {latest_event.get('event', 'N/A')}", className="card-subtitle"),
            html.P(f"Run ID: {latest_event.get('runId', 'N/A')}"),
            html.P(f"UTC Time: {latest_event.get('utcTime', 'N/A')}"),
            html.P(f"Local Time: {utc_to_local(latest_event.get('utcTime', 'N/A'))}"),
            html.Hr(),
            html.H5("Details:"),
            html.Pre(json.dumps(latest_event, indent=2)),
            html.Hr(),
            html.H5("Script:"),
            html.Pre(latest_event.get('trace', {}).get('script', 'N/A')),
            html.Hr(),
            html.H5("Workflow Metadata:"),
            html.Pre(json.dumps(filter_metadata(metadata_info), indent=2)) if metadata_info else "No metadata available"
        ])
    ])
    return details_layout

# Define an endpoint to capture the POST requests
@server.route('/nf-weblog', methods=['POST'])
def nf_weblog():
    if request.is_json:
        content = request.get_json()
        #logging.debug(f'log: {content}')
        workflow_data.append(content)
        return jsonify({"message": "Data received"}), 200
    else:
        return jsonify({"message": "Request was not JSON"}), 400

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8050, host="0.0.0.0")
