import streamlit as st
import pandas as pd
import plotly.express as px

import load_data as df

# st.dataframe(df.df)

# Sample data in dataframe
# "time","client_ip","target_processing_time","target_status_code","request_verb","request_url","request_proto","user_agent","target_group_arn","domain_name"
# "2024-08-22T04:05:40.697348Z","3.208.102.136","0.001","200","POST","https://chat.swiftkanban.com:443/org/10469451525684","HTTP/1.1","NING/1.0","arn:aws:elasticloadbalancing:us-east-1:494145527756:targetgroup/k8s-prod2-skpush-410be80d4e/76fde81018f31bf0","chat.swiftkanban.com"

chart_data = df.df


# Convert the 'time' column to datetime format if it's not already
chart_data['time'] = pd.to_datetime(chart_data['time'])

# Create additional columns
chart_data['hour'] = chart_data['time'].dt.floor('H')
chart_data['hour_of_day'] = chart_data['time'].dt.hour
chart_data['day'] = chart_data['time'].dt.date  # Add a column for the day

# Sidebar for selecting the time unit
st.sidebar.header("Settings")

# Auto-complete for domain_name
domain_filter = st.sidebar.selectbox(
    "Select Domain(s)",
    options=['All'] + list(chart_data['domain_name'].unique()),
    index=0
)

# Text input to include URL patterns
include_patterns = st.sidebar.text_input(
    "Include URL Patterns (comma separated)",
    ""
).strip()

# Text input to exclude URL patterns
exclude_patterns = st.sidebar.text_input(
    "Exclude URL Patterns (comma separated)",
    ""
).strip()

# Convert patterns to lists
include_patterns_list = [pattern.strip() for pattern in include_patterns.split(',') if pattern.strip()]
exclude_patterns_list = [pattern.strip() for pattern in exclude_patterns.split(',') if pattern.strip()]

# Filter data based on domain
if domain_filter == 'All':
    filtered_data = chart_data
else:
    filtered_data = chart_data[chart_data['domain_name'] == domain_filter]

# Filter data based on URL patterns
if include_patterns_list:
    filtered_data = filtered_data[filtered_data['request_url'].apply(lambda url: any(pattern in url for pattern in include_patterns_list))]

# Exclude data based on URL patterns
if exclude_patterns_list:
    for pattern in exclude_patterns_list:
        filtered_data = filtered_data[~filtered_data['request_url'].str.contains(pattern, na=False)]

# Sidebar for selecting the time unit
unit = st.sidebar.radio(
    "Select Time Unit",
    options=["Seconds", "Milliseconds"]
)

# Sidebar for selecting the metric
metric = st.sidebar.selectbox(
    "Select Metric",
    options=["Average", "Min", "Max", "90th Percentile"]
)

# Convert 'target_processing_time' based on selected unit
if unit == "Milliseconds":
    filtered_data['target_processing_time'] = filtered_data['target_processing_time'] * 1000
    unit_label = "(ms)"
else:
    filtered_data['target_processing_time'] = filtered_data['target_processing_time']
    unit_label = "(s)"

# Calculate the hourly metrics based on the selected option for the first chart
if metric == "Average":
    hourly_data = filtered_data.groupby('hour')['target_processing_time'].mean().reset_index()
    hourly_data.rename(columns={'target_processing_time': 'value'}, inplace=True)
elif metric == "Min":
    hourly_data = filtered_data.groupby('hour')['target_processing_time'].min().reset_index()
    hourly_data.rename(columns={'target_processing_time': 'value'}, inplace=True)
elif metric == "Max":
    hourly_data = filtered_data.groupby('hour')['target_processing_time'].max().reset_index()
    hourly_data.rename(columns={'target_processing_time': 'value'}, inplace=True)
elif metric == "90th Percentile":
    hourly_data = filtered_data.groupby('hour')['target_processing_time'].quantile(0.9).reset_index()
    hourly_data.rename(columns={'target_processing_time': 'value'}, inplace=True)

# Create a Plotly line chart for the first chart
fig1 = px.line(
    hourly_data,
    x='hour',
    y='value',
    title=f'Hourly {metric} of Target Processing Time {unit_label}',
    labels={'hour': 'Time', 'value': f'{metric} Target Processing Time {unit_label}'},
    hover_data={'hour': '|%Y-%m-%d %H:%M:%S', 'value': ':,.2f'}
)

# Display the first chart in Streamlit
st.plotly_chart(fig1)

# Calculate the count of requests per hour for the new chart
hourly_request_count = filtered_data.groupby('hour').size().reset_index(name='request_count')

# Create a Plotly line chart for the request count
fig3 = px.line(
    hourly_request_count,
    x='hour',
    y='request_count',
    title='Hourly Request Count',
    labels={'hour': 'Time', 'request_count': 'Request Count'},
    hover_data={'hour': '|%Y-%m-%d %H:%M:%S', 'request_count': ':,.0f'}
)

# Display the request count chart in Streamlit
st.plotly_chart(fig3)

# Prepare data for plotting hourly patterns across all days without aggregation
if metric == "Average":
    daily_data = filtered_data.groupby(['hour_of_day', 'day'])['target_processing_time'].mean().reset_index()
    daily_data.rename(columns={'target_processing_time': 'value'}, inplace=True)
elif metric == "Min":
    daily_data = filtered_data.groupby(['hour_of_day', 'day'])['target_processing_time'].min().reset_index()
    daily_data.rename(columns={'target_processing_time': 'value'}, inplace=True)
elif metric == "Max":
    daily_data = filtered_data.groupby(['hour_of_day', 'day'])['target_processing_time'].max().reset_index()
    daily_data.rename(columns={'target_processing_time': 'value'}, inplace=True)
elif metric == "90th Percentile":
    daily_data = filtered_data.groupby(['hour_of_day', 'day'])['target_processing_time'].quantile(0.9).reset_index()
    daily_data.rename(columns={'target_processing_time': 'value'}, inplace=True)

# Create a Plotly line chart for the daily pattern
fig2 = px.line(
    daily_data,
    x='hour_of_day',
    y='value',
    color='day',  # Use different colors for each day
    title=f'{metric} of Target Processing Time by Hour of the Day {unit_label}',
    labels={'hour_of_day': 'Hour of the Day', 'value': f'{metric} Target Processing Time {unit_label}'},
    hover_data={'hour_of_day': ':.0f', 'value': ':,.2f', 'day': '|%Y-%m-%d'}
)

# Update x-axis to show all hours from 0 to 23
fig2.update_xaxes(
    tickmode='linear',
    tickvals=list(range(24)),  # Show ticks for each hour
    ticktext=[f'{i}:00' for i in range(24)]  # Label ticks with hour in HH:00 format
)

# Display the second chart in Streamlit
st.plotly_chart(fig2)

# Calculate the count of requests per hour of the day
hourly_request_day_count = filtered_data.groupby(['hour_of_day', 'day']).size().reset_index(name='request_count')

# Create a Plotly line chart for the request count by hour of the day
fig4 = px.line(
    hourly_request_day_count,
    x='hour_of_day',
    y='request_count',
    color='day',  # Use different colors for each day
    title='Request Count by Hour of the Day Across All Days',
    labels={'hour_of_day': 'Hour of the Day', 'request_count': 'Request Count'},
    hover_data={'hour_of_day': ':.0f', 'request_count': ':,.0f', 'day': '|%Y-%m-%d'}
)

# Update x-axis to show all hours from 0 to 23
fig4.update_xaxes(
    tickmode='linear',
    tickvals=list(range(24)),  # Show ticks for each hour
    ticktext=[f'{i}:00' for i in range(24)]  # Label ticks with hour in HH:00 format
)

# Display the request count by hour of the day chart in Streamlit
st.plotly_chart(fig4)
