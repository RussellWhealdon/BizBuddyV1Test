import pandas as pd
from datetime import date, timedelta
import calendar
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
import streamlit as st
import plotly.express as px

# Load the secrets for the service account path and property ID
service_account_info = st.secrets["google_service_account"]
property_id = st.secrets["google_service_account"]["property_id"]

# Initialize GA Client using the service account JSON
client = BetaAnalyticsDataClient.from_service_account_info(service_account_info)

# Get todays date
today = date.today().strftime("%Y-%m-%d")

# Get start date
start_date = "30daysAgo"

# Get traffic by source
def fetch_metrics_by_source():
    # Define the request to pull data aggregated by source
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionSource")],  # Only group by source
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="newUsers"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=today)],  # Define date range
    )

    response = client.run_report(request)
    
    # Parse the response and create the dataframe for source-level metrics
    rows = []
    for row in response.rows:
        session_source = row.dimension_values[0].value
        
        # Convert all metrics to numeric values (with coercion to handle non-numeric data)
        active_users = pd.to_numeric(row.metric_values[0].value, errors='coerce')
        sessions = pd.to_numeric(row.metric_values[1].value, errors='coerce')
        pageviews = pd.to_numeric(row.metric_values[2].value, errors='coerce')
        bounce_rate = pd.to_numeric(row.metric_values[3].value, errors='coerce')
        avg_session_duration = pd.to_numeric(row.metric_values[4].value, errors='coerce')
        new_users = pd.to_numeric(row.metric_values[5].value, errors='coerce')
        
        rows.append([
            session_source, active_users, sessions, pageviews, bounce_rate, avg_session_duration, new_users
        ])
    
    # Create DataFrame for metrics by source
    df_source_metrics = pd.DataFrame(rows, columns=[
        'Session Source', 'Total Visitors', 'Sessions', 'Pageviews', 'Bounce Rate', 'Average Session Duration', 'New Users'
    ])
    
    # Convert all numeric columns to proper numeric types
    numeric_cols = ['Total Visitors', 'Sessions', 'Pageviews', 'Bounce Rate', 'Average Session Duration', 'New Users']
    for col in numeric_cols:
        df_source_metrics[col] = pd.to_numeric(df_source_metrics[col], errors='coerce')
    
    # Process data for easier handling
    df_source_metrics.sort_values(by='Session Source', inplace=True)
    
    return df_source_metrics

# Get data by landing page
def fetch_metrics_by_landing_page():
    # Define the request to pull data aggregated by landing page
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="pagePath")],  # Only group by landing page
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="newUsers"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=today)],  # Define date range
    )

    response = client.run_report(request)
    
    # Parse the response and create the dataframe for landing page-level metrics
    rows = []
    for row in response.rows:
        page_path = row.dimension_values[0].value
        
        # Convert all metrics to numeric values (with coercion to handle non-numeric data)
        active_users = pd.to_numeric(row.metric_values[0].value, errors='coerce')
        sessions = pd.to_numeric(row.metric_values[1].value, errors='coerce')
        pageviews = pd.to_numeric(row.metric_values[2].value, errors='coerce')
        bounce_rate = pd.to_numeric(row.metric_values[3].value, errors='coerce')
        avg_session_duration = pd.to_numeric(row.metric_values[4].value, errors='coerce')
        new_users = pd.to_numeric(row.metric_values[5].value, errors='coerce')
        
        rows.append([
            page_path, active_users, sessions, pageviews, bounce_rate, avg_session_duration, new_users
        ])
    
    # Create DataFrame for metrics by landing page
    df_landing_page_metrics = pd.DataFrame(rows, columns=[
        'Page Path', 'Total Visitors', 'Sessions', 'Pageviews', 'Bounce Rate', 'Average Session Duration', 'New Users'
    ])
    
    # Convert all numeric columns to proper numeric types
    numeric_cols = ['Total Visitors', 'Sessions', 'Pageviews', 'Bounce Rate', 'Average Session Duration', 'New Users']
    for col in numeric_cols:
        df_landing_page_metrics[col] = pd.to_numeric(df_landing_page_metrics[col], errors='coerce')
    
    # Process data for easier handling
    df_landing_page_metrics.sort_values(by='Page Path', inplace=True)
    
    return df_landing_page_metrics


#  Get Conversions
def fetch_metrics_by_event():
    # Define the request to pull data aggregated by event name
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="eventName")],  # Group by event name
        metrics=[
            Metric(name="eventCount"),  # Focus on the event count
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=today)],  # Define date range
    )

    response = client.run_report(request)
    
    # Parse the response and create the dataframe for event-level metrics
    rows = []
    for row in response.rows:
        event_name = row.dimension_values[0].value
        
        # Convert event count to numeric (with coercion to handle non-numeric data)
        event_count = pd.to_numeric(row.metric_values[0].value, errors='coerce')
        
        rows.append([event_name, event_count])
    
    # Create DataFrame for metrics by event name
    df_event_metrics = pd.DataFrame(rows, columns=['Event Name', 'Event Count'])
    
    # Convert the 'Event Count' to numeric
    df_event_metrics['Event Count'] = pd.to_numeric(df_event_metrics['Event Count'], errors='coerce')
    
    # Sort data for easier handling
    df_event_metrics.sort_values(by='Event Count', ascending=False, inplace=True)
    
    return df_event_metrics

# Summarize acquisition data
def summarize_acquisition_sources(acquisition_data, event_data):
    # Ensure the Date column is in datetime format and convert to date
    acquisition_data['Date'] = pd.to_datetime(acquisition_data['Date'], errors='coerce').dt.date

    # Get the date 30 days ago
    today = date.today()
    start_of_period = today - timedelta(days=30)
    
    # Filter data for the last 30 days
    monthly_data = acquisition_data[acquisition_data['Date'] >= start_of_period]
    
    # Check if required columns are in the dataframe
    required_cols = ["Session Source", "Sessions", "Bounce Rate"]
    if not all(col in acquisition_data.columns for col in required_cols):
        raise ValueError("Data does not contain required columns.")
    
    # Convert columns to numeric, if possible, and fill NaNs
    monthly_data["Sessions"] = pd.to_numeric(monthly_data["Sessions"], errors='coerce').fillna(0)
    monthly_data["Bounce Rate"] = pd.to_numeric(monthly_data["Bounce Rate"], errors='coerce').fillna(0)
    
    # Merge the traffic data with the event data to include leads
    monthly_data = monthly_data.merge(event_data[['Page Path', 'Event Count']], on='Page Path', how='left')

    # Fill missing values in Event Count with 0 for pages without leads
    monthly_data['Event Count'].fillna(0, inplace=True)

    # Group by Session Source to get aggregated metrics
    source_summary = monthly_data.groupby("Session Source").agg(
        Sessions=("Sessions", "sum"),
        Bounce_Rate=("Bounce Rate", "mean"),
        Conversions=("Event Count", "sum")  # Use Event Count for conversions (leads)
    ).reset_index()

    # Calculate Conversion Rate (%) for each source
    source_summary["Conversion Rate (%)"] = (source_summary["Conversions"] / source_summary["Sessions"] * 100).round(2)

    # Sort by Sessions in descending order
    source_summary = source_summary.sort_values(by="Sessions", ascending=False)
    
    return source_summary

# Get landing page summary
def summarize_landing_pages(acquisition_data, event_data):
    # Check if required columns are in the dataframe
    required_cols = ["Page Path", "Sessions", "Bounce Rate", "Total Visitors", "Pageviews", "Average Session Duration"]
    if not all(col in acquisition_data.columns for col in required_cols):
        raise ValueError("Data does not contain required columns.")
    
    # Convert columns to numeric, if possible, and fill NaNs
    numeric_cols = ["Sessions", "Bounce Rate", "Total Visitors", "Pageviews", "Average Session Duration"]
    for col in numeric_cols:
        acquisition_data[col] = pd.to_numeric(acquisition_data[col], errors='coerce').fillna(0)

    # Merge with event data to include leads
    page_summary = acquisition_data.merge(event_data[['Page Path', 'Event Count']], on='Page Path', how='left')

    # Fill missing values in Event Count with 0 for pages without leads
    page_summary['Event Count'].fillna(0, inplace=True)

    # Group by Page Path to get aggregated metrics
    page_summary = page_summary.groupby("Page Path").agg(
        Sessions=("Sessions", "sum"),
        Total_Visitors=("Total Visitors", "sum"),
        Pageviews=("Pageviews", "sum"),
        Avg_Session_Duration=("Average Session Duration", "mean"),
        Bounce_Rate=("Bounce Rate", "mean"),
        Conversions=("Event Count", "sum")  # Use Event Count for conversions (leads)
    ).reset_index()

    # Calculate Conversion Rate
    page_summary["Conversion Rate (%)"] = (page_summary["Conversions"] / page_summary["Sessions"] * 100).round(2)

    # Sort by Sessions in descending order
    page_summary = page_summary.sort_values(by="Sessions", ascending=False)
    
    return page_summary


# Get this months summary
def summarize_monthly_data(acquisition_data, event_data):
    # Ensure the Date column is in datetime format, then convert to date
    if 'Date' not in acquisition_data.columns:
        raise ValueError("Data does not contain a 'Date' column.")
    
    acquisition_data['Date'] = pd.to_datetime(acquisition_data['Date'], errors='coerce').dt.date

    # Get the date 30 days ago
    today = date.today()
    start_of_period = today - timedelta(days=30)
    
    # Filter data for the last 30 days
    monthly_data = acquisition_data[acquisition_data['Date'] >= start_of_period]
    
    # Check if required columns are in the dataframe
    required_cols = ["Total Visitors", "New Users", "Sessions", "Average Session Duration", "Session Source"]
    if not all(col in monthly_data.columns for col in required_cols):
        raise ValueError("Data does not contain required columns.")
    
    # Convert columns to numeric, if possible, and fill NaNs
    numeric_cols = ["Total Visitors", "New Users", "Sessions", "Average Session Duration"]
    for col in numeric_cols:
        monthly_data[col] = pd.to_numeric(monthly_data[col], errors='coerce').fillna(0)
    
    # Merge with event data to include leads (Event Count)
    monthly_data = monthly_data.merge(event_data[['Page Path', 'Event Count']], on='Page Path', how='left')

    # Convert 'Event Count' to numeric, coerce non-numeric values to NaN, then fill NaN with 0
    monthly_data['Event Count'] = pd.to_numeric(monthly_data['Event Count'], errors='coerce').fillna(0)

    # Calculate total metrics for the last 30 days
    total_visitors = monthly_data["Total Visitors"].sum()
    new_visitors = monthly_data["New Users"].sum()
    total_sessions = monthly_data["Sessions"].sum()
    total_leads = monthly_data["Event Count"].sum()  # Sum of Event Count for leads

    # Calculate average metrics for the last 30 days
    avg_time_on_site = monthly_data["Average Session Duration"].mean().round(2)
    
    # Create a summary DataFrame
    summary_df = pd.DataFrame({
        "Metric": ["Total Visitors", "New Visitors", "Total Sessions", "Total Leads", "Average Session Duration"],
        "Value": [total_visitors, new_visitors, total_sessions, total_leads, avg_time_on_site]
    })

    # Summarize acquisition metrics (using Event Count for leads)
    acquisition_summary = monthly_data.groupby("Session Source").agg(
        Visitors=("Total Visitors", "sum"),
        Sessions=("Sessions", "sum"),
        Leads=("Event Count", "sum")  # Use Event Count for conversions (leads)
    ).reset_index()
    
    return summary_df, acquisition_summary


# Summarize last month data
def summarize_last_month_data(acquisition_data, event_data):
    # Ensure the Date column is in datetime format, then convert to date
    if 'Date' not in acquisition_data.columns:
        raise ValueError("Data does not contain a 'Date' column.")
    
    acquisition_data['Date'] = pd.to_datetime(acquisition_data['Date'], errors='coerce').dt.date

    # Calculate the first and last day of the previous month
    today = date.today()
    first_day_of_this_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_this_month - timedelta(days=1)
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    
    # Filter data for the previous month
    last_month_data = acquisition_data[
        (acquisition_data['Date'] >= first_day_of_last_month) & 
        (acquisition_data['Date'] <= last_day_of_last_month)
    ]
    
    # Check if required columns are in the dataframe
    required_cols = ["Total Visitors", "New Users", "Sessions", "Average Session Duration", "Session Source"]
    if not all(col in last_month_data.columns for col in required_cols):
        raise ValueError("Data does not contain required columns.")
    
    # Convert columns to numeric, if possible, and fill NaNs
    numeric_cols = ["Total Visitors", "New Users", "Sessions", "Average Session Duration"]
    for col in numeric_cols:
        last_month_data[col] = pd.to_numeric(last_month_data[col], errors='coerce').fillna(0)
    
    # Merge with event data to include leads (Event Count)
    last_month_data = last_month_data.merge(event_data[['Page Path', 'Event Count']], on='Page Path', how='left')

    # Fill missing values in Event Count with 0 for pages without leads
    last_month_data['Event Count'].fillna(0, inplace=True)

    # Set the 'Conversions' column to 0 for all pages except the Contact page
    last_month_data['Conversions'] = last_month_data.apply(
        lambda row: row['Event Count'] if row['Page Path'] == '/contact' else 0, axis=1
    )

    # Check if the 'Event Count' column is numeric after conversion
    if not pd.api.types.is_numeric_dtype(last_month_data['Event Count']):
        raise ValueError("Event Count column contains non-numeric data.")

    # Calculate total metrics for last month
    total_visitors = last_month_data["Total Visitors"].sum()
    new_visitors = last_month_data["New Users"].sum()
    total_sessions = last_month_data["Sessions"].sum()
    total_leads = last_month_data["Conversions"].sum()  # Sum of Conversions for leads

    # Calculate average metrics for last month
    avg_time_on_site = last_month_data["Average Session Duration"].mean().round(2)
    
    # Create a summary dataframe
    summary_df = pd.DataFrame({
        "Metric": ["Total Visitors", "New Visitors", "Total Sessions", "Total Leads", "Average Session Duration"],
        "Value": [total_visitors, new_visitors, total_sessions, total_leads, avg_time_on_site]
    })

    # Summarize acquisition metrics (using Event Count for leads)
    acquisition_summary = last_month_data.groupby("Session Source").agg(
        Visitors=("Total Visitors", "sum"),
        Sessions=("Sessions", "sum"),
        Leads=("Conversions", "sum")  # Use Conversions for leads
    ).reset_index()
    
    return summary_df, acquisition_summary

# Generate all metrics
def generate_all_metrics_copy(current_summary_df, last_month_summary_df):
    # List of metrics and their descriptions
    metrics = {
        "Total Visitors": "the number of people that have visited your site.",
        "New Visitors": "the number of people visiting your site for the first time.",
        "Total Sessions": "the total number of times people have visited your site this month, including repeat visits.",
        "Total Leads": "the number of leads generated this month.",
        "Average Session Duration": "the average amount of time users spent on your site per session."
    }
    
    st.markdown(
        "<span style='font-size:25px;'>📊 **Data Overview: Last 30 Days**</span>", 
        unsafe_allow_html=True
    )
    
    for metric_name, description in metrics.items():
        # Extract metric values for the current and last month
        current_value = current_summary_df.loc[current_summary_df['Metric'] == metric_name, 'Value'].values[0]
        last_month_value = last_month_summary_df.loc[last_month_summary_df['Metric'] == metric_name, 'Value'].values[0]
        
        # For "Total Leads", make sure it only counts the leads from the Contact page
        if metric_name == "Total Leads":
            current_value = current_summary_df.loc[current_summary_df['Metric'] == "Total Leads", 'Value'].values[0]
            last_month_value = last_month_summary_df.loc[last_month_summary_df['Metric'] == "Total Leads", 'Value'].values[0]

        # Calculate the percentage change
        if last_month_value > 0:
            percentage_change = ((current_value - last_month_value) / last_month_value) * 100
        else:
            percentage_change = 0  # Avoid division by zero
        
        # Determine the direction of change (up or down)
        change_direction = "up" if percentage_change > 0 else "down"
        percentage_change = abs(percentage_change)
        color = "green" if change_direction == "up" else "red"  # Green for positive, red for negative
        
        # Customize the metric display for "Average Session Duration"
        if metric_name == "Average Session Duration":
            display_metric = f"**Average Time on Site: {round(current_value)} seconds**"
        else:
            display_metric = f"**{round(current_value)} {metric_name}**"
        
        # Generate the display copy for each metric
        st.markdown(
            f"{display_metric} - _{description}_<br>"
            f"<span style='font-size: smaller;'>This is {change_direction} "
            f"<span style='color:{color};'>{percentage_change:.2f}%</span> from last month.</span>", 
            unsafe_allow_html=True
        )


def plot_acquisition_pie_chart_plotly(acquisition_summary):
    # Filter data for pie chart
    source_data = acquisition_summary[['Session Source', 'Visitors']].copy()
    source_data = source_data[source_data['Visitors'] > 0]  # Exclude sources with no visitors
    
    # Create pie chart with Plotly
    fig = px.pie(
        source_data,
        names='Session Source',
        values='Visitors',
        #title='Traffic Sources Breakdown',
        hole=0.4,  # Optional: Donut style
        labels={'Session Source': 'Source', 'Visitors': 'Visitors'}
    )
    
    # Update layout to place labels outside
    fig.update_traces(textposition='outside', textinfo='label+percent', showlegend=False)

    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def describe_top_sources(acquisition_summary):
    # Sort by Visitors and take the top 3
    top_sources = acquisition_summary.sort_values(by='Visitors', ascending=False).head(3)
    
    # Hard-coded descriptions for specific sources
    descriptions = {
        "google": (
            "_A visitor coming from Google means they reached your site through a Google service. "
            "This could include organic or paid search, a link from Gmail, Google Drive, or even "
            "Google Ads and other platforms in the Google ecosystem._"
        ),
        "(direct)": (
            "_A visitor coming from (direct) means they typed your website URL directly into their browser, "
            "clicked a bookmark, or came from an untracked link like a non-HTTP email or offline document._"
        ),
        "manage.wix.com": (
            "_A visitor coming from manage.wix.com indicates they were redirected from the Wix site editor, "
            "often during testing or setup._"
        )
    }
    
    # Display each top source with description
    st.markdown(
    "<span style='font-size:18px;'>**Top Sources Overview**</span>", 
    unsafe_allow_html=True
    )
    for _, row in top_sources.iterrows():
        source = row['Session Source']
        visitors = row['Visitors']
        
        st.markdown(f"**{source} - {visitors} visitors**")
        st.markdown(f"{descriptions.get(source, 'Description not available for this source.')}")

def generate_page_summary(landing_page_summary):
    # Map page paths to friendly names
    page_name_map = {
        "/": "Home",
        "/contact": "Contact",
        "/ratesinsurance": "Rates & Insurance",
        "/about": "About",
        "/faqs": "FAQs",
        "/adults-nutrition-counseling": "Adults",
        "/teens-nutrition-counseling": "Teens"
    }

    # Filter the DataFrame to only include the specified pages
    filtered_summary = landing_page_summary[landing_page_summary["Page Path"].isin(page_name_map.keys())]

    # Rename Page Path to friendly names
    filtered_summary["Page Name"] = filtered_summary["Page Path"].map(page_name_map)

    # Initialize a summary string to track all page info for LLM
    llm_summary = "### Page Performance Summary\n\n"

    # Display summary for each relevant page and append to LLM summary
    for _, row in filtered_summary.iterrows():
        page_name = row["Page Name"]
        visitors = row["Total_Visitors"]
        sessions = row["Sessions"]
        avg_session_duration = round(row["Avg_Session_Duration"], 2)
        conversion_rate = (
            f"|&nbsp;&nbsp;Conversion Rate: {row['Conversion Rate (%)']}%" if page_name == "Contact" else ""
        )
        
        # Display the page summary
        st.markdown(
            f"**{page_name}**<br>"
            f"Visitors: {visitors} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Sessions: {sessions} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Average Session Duration: {avg_session_duration} seconds &nbsp;&nbsp; "
            f"{conversion_rate}",
            unsafe_allow_html=True
        )
        
        # Append to LLM summary
        llm_summary += (
            f"**{page_name}**: Visitors: {visitors}, "
            f"Sessions: {sessions}, "
            f"Average Session Duration: {avg_session_duration} seconds"
        )
        if page_name == "Contact":
            llm_summary += f", Conversion Rate: {row['Conversion Rate (%)']}%"
        llm_summary += "\n\n"

    # Store LLM summary in session state for later use
    st.session_state["page_summary_llm"] = llm_summary
