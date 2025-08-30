import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from groq import Groq
import re
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="FloatChat - ARGO Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the Groq client
client = Groq(api_key="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")

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            "postgresql://neondb_owner:npg_qV9a3dQRAeBm@ep-still-field-a17hi4xm-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# System prompt for the LLM
system_prompt = """
You are FloatChat, an AI-powered conversational agent for ARGO ocean data exploration and visualization. 
You are connected to a PostgreSQL database with the schema:

Table: argo_floats
Columns:
- id (int, primary key)
- platform_number (varchar): unique float identifier
- cycle_number (int): profile cycle number
- measurement_time (timestamp): date & time of observation
- latitude (double precision)
- longitude (double precision)
- pressure (double precision): depth in decibars
- temperature (double precision): temperature (°C)
- salinity (double precision): salinity (PSU)
- data_quality (varchar)
- region (varchar, default 'Indian Ocean')
- data_source (varchar)
- created_at (timestamp)

Your role:
1. Take user questions in natural language.
2. Translate them into valid SQL queries on the `argo_floats` table.
3. If the query requires spatial/temporal filtering, use latitude, longitude, and measurement_time.
4. Always limit results for readability (e.g., LIMIT 100) unless the user requests full output.
5. Provide the answer in natural language, followed by tabular results. 
6. If the question asks for visualization:
   - For trends over time → return a line plot (time vs variable).
   - For spatial patterns → return a map scatter (lat vs lon).
   - For vertical profiles (pressure vs temperature/salinity) → return depth plots.
7. If the user asks vague questions, guide them by suggesting possible queries.

Always stay grounded in the database content. Do not hallucinate.

Output your response in the following format:
<thinking>
[Your reasoning about the query and what SQL to generate]
</thinking>

<sql>
[Your SQL query here]
</sql>

<response>
[Your natural language response to the user]
</response>
"""

# Function to extract SQL from LLM response
def extract_sql(response):
    sql_match = re.search(r'<sql>(.*?)</sql>', response, re.DOTALL)
    if sql_match:
        return sql_match.group(1).strip()
    return None

# Function to execute SQL query and return results as DataFrame
def execute_sql_query(sql_query):
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
        conn.close()
        return None

# Function to create a map visualization
def create_map(df):
    if df is None or df.empty or 'latitude' not in df.columns or 'longitude' not in df.columns:
        return None
    
    # Calculate center of the map
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=3)
    
    # Add markers for each data point
    for _, row in df.iterrows():
        # Create popup content
        popup_content = f"""
        <b>Float:</b> {row.get('platform_number', 'N/A')}<br>
        <b>Time:</b> {row.get('measurement_time', 'N/A')}<br>
        <b>Temp:</b> {row.get('temperature', 'N/A')}°C<br>
        <b>Salinity:</b> {row.get('salinity', 'N/A')} PSU<br>
        <b>Pressure:</b> {row.get('pressure', 'N/A')} dbar
        """
        
        # Color code by temperature if available
        if 'temperature' in df.columns:
            temp = row.get('temperature', 20)
            if temp < 10:
                color = 'blue'
            elif temp < 20:
                color = 'green'
            elif temp < 25:
                color = 'orange'
            else:
                color = 'red'
        else:
            color = 'blue'
        
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"Float: {row.get('platform_number', 'N/A')}",
            icon=folium.Icon(color=color, icon='tint', prefix='fa')
        ).add_to(m)
    
    return m

# Function to generate profile plot
def create_profile_plot(df):
    if df is None or df.empty or 'pressure' not in df.columns:
        return None
    
    fig, ax1 = plt.subplots(figsize=(8, 10))
    
    # Plot temperature if available
    if 'temperature' in df.columns:
        color = 'tab:red'
        ax1.set_xlabel('Temperature (°C)', color=color)
        ax1.plot(df['temperature'], df['pressure'], color=color, marker='o', linestyle='-', label='Temperature')
        ax1.tick_params(axis='x', labelcolor=color)
        ax1.invert_yaxis()  # Invert y-axis for depth
    
    # Create second axis for salinity if available
    if 'salinity' in df.columns:
        ax2 = ax1.twiny()
        color = 'tab:blue'
        ax2.set_xlabel('Salinity (PSU)', color=color)
        ax2.plot(df['salinity'], df['pressure'], color=color, marker='s', linestyle='--', label='Salinity')
        ax2.tick_params(axis='x', labelcolor=color)
    
    ax1.set_ylabel('Pressure (dbar)')
    ax1.grid(True)
    plt.title('Vertical Profile')
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    if 'salinity' in df.columns:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    else:
        ax1.legend(loc='upper right')
    
    return fig

# Function to generate time series plot
def create_time_series(df):
    if df is None or df.empty or 'measurement_time' not in df.columns:
        return None
    
    # Convert to datetime if needed
    if df['measurement_time'].dtype == 'object':
        df['measurement_time'] = pd.to_datetime(df['measurement_time'])
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot temperature if available
    if 'temperature' in df.columns:
        color = 'tab:red'
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Temperature (°C)', color=color)
        ax1.plot(df['measurement_time'], df['temperature'], color=color, marker='o', linestyle='-', label='Temperature')
        ax1.tick_params(axis='y', labelcolor=color)
    
    # Create second axis for salinity if available
    if 'salinity' in df.columns:
        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('Salinity (PSU)', color=color)
        ax2.plot(df['measurement_time'], df['salinity'], color=color, marker='s', linestyle='--', label='Salinity')
        ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Time Series')
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    if 'salinity' in df.columns:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax1.legend(loc='upper left')
    
    plt.tight_layout()
    return fig

# Main function to process user queries
def process_user_query(user_query):
    # Prepare messages for the LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    # Get response from LLM
    try:
        with st.spinner("Generating SQL query..."):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )
        
        llm_response = completion.choices[0].message.content
        
        # Extract SQL from response
        sql_query = extract_sql(llm_response)
        
        if not sql_query:
            st.error("I couldn't generate a valid SQL query for your request. Please try rephrasing.")
            return None, None, None
        
        st.code(sql_query, language="sql")
        
        # Execute the SQL query
        with st.spinner("Executing query..."):
            df = execute_sql_query(sql_query)
        
        if df is None or df.empty:
            st.warning("No data found for your query. Please try different parameters.")
            return None, None, None
        
        # Extract the natural language response from LLM
        response_match = re.search(r'<response>(.*?)</response>', llm_response, re.DOTALL)
        natural_response = response_match.group(1).strip() if response_match else "Here are the results of your query:"
        
        return natural_response, df, sql_query
        
    except Exception as e:
        st.error(f"Error processing your request: {str(e)}")
        return None, None, None

# Main app
def main():
    # Sidebar
    with st.sidebar:
        st.title("FloatChat 🌊")
        st.markdown("ARGO Data Explorer")
        
        # Query input
        user_query = st.text_area(
            "Enter your query about ARGO data:",
            height=100,
            placeholder="e.g., Show me temperature profiles for floats near the equator in the last month"
        )
        
        # Process button
        process_btn = st.button("Process Query", type="primary")
        
        # Example queries
        st.markdown("### Example Queries")
        examples = [
            "Show me the last 10 temperature measurements in the Indian Ocean",
            "Plot salinity vs pressure for float 2902769",
            "Which floats recorded the highest temperatures in the last month?",
            "Show me a map of all float measurements with salinity above 36 PSU"
        ]
        
        for example in examples:
            if st.button(example, key=example):
                user_query = example
                process_btn = True
    
    # Main content
    st.title("ARGO Float Data Dashboard")
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'sql' not in st.session_state:
        st.session_state.sql = None
    
    # Process query if button is clicked
    if process_btn and user_query:
        natural_response, df, sql_query = process_user_query(user_query)
        if df is not None:
            st.session_state.results = natural_response
            st.session_state.df = df
            st.session_state.sql = sql_query
    
    # Display results if available
    if st.session_state.df is not None:
        # Display natural language response
        st.markdown("### Results")
        st.write(st.session_state.results)
        
        # Display data
        st.dataframe(st.session_state.df, use_container_width=True)
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["Map", "Profile", "Time Series", "Raw Data"])
        
        with tab1:
            # Create map
            st.subheader("Float Locations")
            map_obj = create_map(st.session_state.df)
            if map_obj:
                folium_static(map_obj, width=1000, height=600)
            else:
                st.info("No location data available for mapping.")
        
        with tab2:
            # Create profile plot
            st.subheader("Vertical Profile")
            profile_fig = create_profile_plot(st.session_state.df)
            if profile_fig:
                st.pyplot(profile_fig)
            else:
                st.info("No pressure data available for profile plot.")
        
        with tab3:
            # Create time series
            st.subheader("Time Series")
            time_fig = create_time_series(st.session_state.df)
            if time_fig:
                st.pyplot(time_fig)
            else:
                st.info("No time data available for time series plot.")
        
        with tab4:
            # Show raw data
            st.subheader("Raw Data")
            st.dataframe(st.session_state.df, use_container_width=True)
            st.download_button(
                label="Download data as CSV",
                data=st.session_state.df.to_csv(index=False),
                file_name="argo_data.csv",
                mime="text/csv",
            )
    
    # Display database info
    with st.expander("Database Information"):
        conn = get_db_connection()
        if conn:
            try:
                # Get table info
                table_info = pd.read_sql("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'argo_floats'
                    ORDER BY ordinal_position;
                """, conn)
                
                st.write("Table Schema:")
                st.dataframe(table_info)
                
                # Get some stats
                row_count = pd.read_sql("SELECT COUNT(*) as count FROM argo_floats;", conn)
                min_date = pd.read_sql("SELECT MIN(measurement_time) as min_date FROM argo_floats;", conn)
                max_date = pd.read_sql("SELECT MAX(measurement_time) as max_date FROM argo_floats;", conn)
                
                st.write("Database Statistics:")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Records", f"{row_count['count'].iloc[0]:,}")
                col2.metric("Earliest Measurement", min_date['min_date'].iloc[0].strftime('%Y-%m-%d'))
                col3.metric("Latest Measurement", max_date['max_date'].iloc[0].strftime('%Y-%m-%d'))
                
                conn.close()
            except Exception as e:
                st.error(f"Error retrieving database info: {e}")

if __name__ == "__main__":
    main()
