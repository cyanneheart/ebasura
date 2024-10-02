import uuid
import os
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from ..engine import db
from datetime import datetime, timedelta

def create_dash(server):
    # Create Dash app
    dash = Dash(__name__, server=server, url_base_pathname='/dash/')

    # Define the layout of the Dash app
    dash.layout = html.Div([
        dcc.Dropdown(id='dropdown-selection', 
                     options=[{'label': 'Recyclable', 'value': 'Recyclable'},
                              {'label': 'Non-recyclable', 'value': 'Non-recyclable'}],
                     value='Recyclable'),
        dcc.Graph(id='graph-content'),
        dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
    ])

    # Define the callback to update the graph based on selected waste type
    @dash.callback(
        Output('graph-content', 'figure'),
        [Input('dropdown-selection', 'value'),
         Input('interval-component', 'n_intervals')]
    )
    def update_graph(waste_type, n):
        # SQL query to get the earliest available data date from the database
        sql_start_date = """
        SELECT MIN(DATE(waste_data.timestamp)) AS start_date
        FROM waste_data
        INNER JOIN waste_type ON waste_type.waste_type_id = waste_data.waste_type_id
        WHERE waste_type.name = %s;
        """
        # Fetch the start date from the database
        result = db.fetch(sql_start_date, (waste_type,))
        start_date = result[0]['start_date'] if result else datetime.now().date()

        # Get the current date
        today = datetime.now().date()

        # SQL query to get the waste data, grouping by day from the start date to today
        sql = """
        SELECT DATE(waste_data.timestamp) AS date, COUNT(waste_data.waste_type_id) as count
        FROM waste_data
        INNER JOIN waste_type ON waste_type.waste_type_id = waste_data.waste_type_id
        WHERE waste_type.name = %s
        AND waste_data.timestamp BETWEEN %s AND %s
        GROUP BY DATE(waste_data.timestamp)
        ORDER BY DATE(waste_data.timestamp);
        """
        
        # Fetch the data from the database for the range from start date to today
        rows = db.fetch(sql, (waste_type, start_date, today))
        
        # If no data returned, handle empty data gracefully
        if not rows:
            return px.line()  # Return an empty graph if no data is found

        # Convert rows to a DataFrame
        df = pd.DataFrame(rows, columns=['date', 'count'])
        
        # Get the data up to the current day + n_intervals (making it progressive)
        current_date_range = df[df['date'] <= start_date + timedelta(days=n)]

        # Create a time series line chart with the fetched data (waste per day)
        fig = px.line(current_date_range, x='date', y='count', title=f'Waste Data per Day for {waste_type}')
        fig.update_layout(transition_duration=500)

        return fig

    return dash
