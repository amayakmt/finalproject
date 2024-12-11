import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pydeck as pdk

# Load dataset
file_name = "skyscrapers.csv"
df = pd.read_csv(file_name)

# Data cleaning and preparation
df['location.city'] = df['location.city'].fillna('Unknown')
df.columns = df.columns.str.replace('.', '_')
df['status_completed_year'] = df['status_completed_year'].replace(0, np.nan)

# Streamlit UI Customization
st.markdown(
    """
    <style>
    body {
        background-color: #191919;
        color: #a18972;
        font-family: 'Arial', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #191919;
        color: #a18972;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #a18972;
    }

    input, textarea {
        color: #a18972;
        background-color: #292929;
    }

    button {
        background-color: #a18972 !important;
        color: #191919 !important;
    }

    table {
        color: #a18972;
        background-color: #292929;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Filters
st.sidebar.header('Filter Options')
year_range = st.sidebar.slider(
    'Year Built Range',
    int(df['status_completed_year'].min()),
    int(df['status_completed_year'].max()),
    (1850, 2020)
)
height_range = st.sidebar.slider(
    'Height Range (m)',
    int(df['statistics_height'].min()),
    int(df['statistics_height'].max()),
    (0, 1609)
)
city_filter = st.sidebar.multiselect(
    'Select Cities (or deselect all for all cities)',
    options=df['location_city'].unique(),
    default=None
)

# Apply Filters
filtered_df = df[
    (df['status_completed_year'] >= year_range[0]) &
    (df['status_completed_year'] <= year_range[1]) &
    (df['statistics_height'] >= height_range[0]) &
    (df['statistics_height'] <= height_range[1])
]
if city_filter:
    filtered_df = filtered_df[filtered_df['location_city'].isin(city_filter)]

# Drop unwanted columns
columns_to_exclude = ['id', 'location_city_id', 'location_country id', 'purposes_abandoned',
                      'purposes_air traffic control tower', 'purposes_belltower', 'purposes_bridge',
                      'purposes_casino', 'purposes_commercial', 'purposes_education', 'purposes_exhibition',
                      'purposes_government', 'purposes_hospital', 'purposes_hotel', 'purposes_industrial',
                      'purposes_library', 'purposes_multiple', 'purposes_museum', 'purposes_observation',
                      'purposes_office', 'purposes_other', 'purposes_religious', 'purposes_residential',
                      'purposes_retail', 'purposes_serviced apartments', 'purposes_telecommunications',
                      'status_completed_is completed', 'status_started_is started']
filtered_df = filtered_df.drop(columns=columns_to_exclude, axis=1)

# Tabs for better organization
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Filtered Data", "3D Map", "Statistics", "Top Cities", "Trend Over Time", "Download Data"
])

# Tab 1: Filtered Data
with tab1:
    st.subheader("Filtered Data")
    st.write(filtered_df)

# Tab 2: 3D Map that demonstrates heights of skyscrapers
with tab2:
    st.subheader("3D Map of Skyscraper Heights")

    # Round the height to the nearest meter
    filtered_df['statistics_height'] = round(filtered_df['statistics_height'], 0)

    # Ensure latitude and longitude columns exist
    if not filtered_df.empty and 'location_latitude' in filtered_df.columns and 'location_longitude' in filtered_df.columns:
        # Dropdown to select a city
        unique_cities = filtered_df['location_city'].unique()
        selected_city = st.selectbox("Select a City", options=unique_cities, index=0)

        # Filter data for the selected city
        city_data = filtered_df[filtered_df['location_city'] == selected_city]

        # Set map view to the selected city
        view_state = pdk.ViewState(
            latitude=city_data['location_latitude'].mean(),
            longitude=city_data['location_longitude'].mean(),
            zoom=12,  # Zoom level for the selected city
            pitch=50  # 3D pitch angle
        )

        # Define the 3D layer
        layer = pdk.Layer(
            "ColumnLayer",
            data=city_data,
            get_position=["location_longitude", "location_latitude"],
            get_elevation="statistics_height",  # Skyscraper height
            elevation_scale=5,
            radius=100,
            get_fill_color="[161, 137, 114, 200]",  # RGBA matching #a18972
            pickable=True,
            auto_highlight=True,
        )

        # Render the deck.gl map with a dark theme
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v10",  # Dark map style
            tooltip={"text": "Height: {statistics_height}m\nCity: {location_city}"}
        )
        st.pydeck_chart(r)
    else:
        st.write("No data available or missing latitude/longitude columns for visualization.")

# Tab 3: Statistics
with tab3:
    st.subheader("Skyscraper Statistics")

    # Filter out rows where height is 0
    filtered_df_nonzero = filtered_df[filtered_df['statistics_height'] > 0]

    # Perform calculations on the filtered data
    summary = {
        "Tallest Skyscraper Height (m)": filtered_df_nonzero['statistics_height'].max(),
        "Shortest Skyscraper Height (m)": filtered_df_nonzero['statistics_height'].min(),
        "Average Skyscraper Height (m)": round(filtered_df_nonzero['statistics_height'].mean(),2),
        "Median Skyscraper Height (m)": filtered_df_nonzero['statistics_height'].median(),
        "Number of Skyscrapers": filtered_df_nonzero.shape[0],
    }

    # Display the summary as a table
    st.write(pd.DataFrame.from_dict(summary, orient='index', columns=["Value"]))

# Tab 4: Top Cities Visualization
with tab4:
    st.subheader("Top Cities with the Most Skyscrapers")
    city_counts = filtered_df['location_city'].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(city_counts.index, city_counts.values, color='#a18972')
    fig.patch.set_facecolor("#191919")
    ax.set_facecolor("#191919")
    ax.set_xlabel("City", fontsize=14, color="#a18972")
    ax.set_ylabel("Number of Skyscrapers", fontsize=14, color="#a18972")
    plt.xticks(rotation=45, ha="right", fontsize=12, color="#a18972")
    plt.yticks(fontsize=12, color="#a18972")
    ax.grid(axis='y', linestyle='--', linewidth=0.7, alpha=0.5, color="#a18972")
    st.pyplot(fig)

# Tab 5: Trend Over Time Visualization
with tab5:
    st.subheader("Trend of Skyscraper Construction Over Time")
    year_counts = filtered_df['status_completed_year'].dropna().value_counts().sort_index()
    all_years = pd.Series(0, index=pd.RangeIndex(start=int(year_counts.index.min()), stop=2025))
    year_counts = all_years.add(year_counts, fill_value=0).sort_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(year_counts.index, year_counts.values, color='#a18972', linewidth=2)
    fig.patch.set_facecolor("#191919")
    ax.set_facecolor("#191919")
    ax.set_xlabel("Year", fontsize=14, color="#a18972")
    ax.set_ylabel("Number of Skyscrapers", fontsize=14, color="#a18972")
    plt.xticks(rotation=45, ha="right", fontsize=12, color="#a18972")
    plt.yticks(fontsize=12, color="#a18972")
    ax.grid(axis='y', linestyle='--', linewidth=0.7, alpha=0.5, color="#a18972")
    st.pyplot(fig)

# Tab 6: Download Data
with tab6:
    st.subheader("Download Filtered Data")
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="filtered_skyscrapers.csv",
            mime="text/csv"
        )
    else:
        st.write("No data available for download.")
