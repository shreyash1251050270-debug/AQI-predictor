"""
AQI India — Streamlit Web App
==============================
Run: streamlit run app.py
Needs: aqi_weather_monthly.csv in the same folder (from 01_data_cleaning.py)

Install: pip install streamlit pandas plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AQI India — Air Quality Analysis",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background: #0f1a12; }
  h1, h2, h3 { font-family: 'Georgia', serif; }
  .metric-label { font-size: 0.75rem; color: #7aab82; text-transform: uppercase; letter-spacing: 0.1em; }
  .big-metric { font-size: 3rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ── AQI COLOUR HELPER ────────────────────────────────────────────────────────
def aqi_color(val):
    if val <= 50:   return "#00e676"
    if val <= 100:  return "#aeea00"
    if val <= 200:  return "#ffd600"
    if val <= 300:  return "#ff6d00"
    if val <= 400:  return "#dd2c00"
    return "#aa00ff"

def aqi_category(val):
    if val <= 50:   return "Good ✅"
    if val <= 100:  return "Satisfactory 🟡"
    if val <= 200:  return "Moderate ⚠️"
    if val <= 300:  return "Poor 🔴"
    if val <= 400:  return "Very Poor 🟣"
    return "Severe ☠️"

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("aqi_weather_monthly.csv")
        return df
    except FileNotFoundError:
        # Demo data if CSV not yet generated
        import numpy as np
        cities = ["Delhi","Mumbai","Bangalore","Kolkata","Chennai",
                  "Hyderabad","Ahmedabad","Lucknow","Patna","Pune"]
        months = list(range(1, 13))
        rows = []
        base = {"Delhi":220,"Mumbai":90,"Bangalore":80,"Kolkata":155,
                "Chennai":72,"Hyderabad":88,"Ahmedabad":130,
                "Lucknow":185,"Patna":195,"Pune":100}
        season_factor = {1:1.4,2:1.25,3:1.0,4:0.85,5:0.8,6:0.65,
                         7:0.55,8:0.52,9:0.6,10:0.92,11:1.15,12:1.45}
        for city in cities:
            for month in months:
                aqi = int(base[city] * season_factor[month] + np.random.randint(-10, 10))
                rows.append({
                    "City": city, "Month": month,
                    "Month_Name": ["Jan","Feb","Mar","Apr","May","Jun",
                                   "Jul","Aug","Sep","Oct","Nov","Dec"][month-1],
                    "Year": 2019, "AQI": aqi,
                    "PM2.5": aqi*0.58, "PM10": aqi*1.2,
                    "NO2": aqi*0.22,   "SO2":  aqi*0.07,
                    "Temp_C":    [14,17,25,32,36,37,34,33,30,26,19,13][month-1],
                    "Humidity_pct":[70,62,52,38,32,52,78,82,70,52,58,72][month-1],
                    "Wind_kmh":  [8,9,11,13,14,18,20,19,16,11,8,7][month-1],
                    "Rainfall_mm":[20,15,8,2,5,65,195,215,125,18,2,12][month-1],
                    "Season": (lambda m: "Winter" if m in [12,1,2]
                               else "Summer" if m in [3,4,5]
                               else "Monsoon" if m in [6,7,8,9]
                               else "Post-Monsoon")(month),
                    "AQI_Category": aqi_category(aqi).split(" ")[0],
                })
        return pd.DataFrame(rows)

df = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("🌿 AQI India")
st.sidebar.markdown("Air Quality & Weather Analysis")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", [
    "🔍 City Lookup",
    "📊 City Comparison",
    "🗓️ Monthly Heatmap",
    "📈 Regression Insights",
    "🗺️ Overview",
])

years = sorted(df["Year"].unique()) if "Year" in df.columns else [2019]
sel_year = st.sidebar.selectbox("Year", ["All"] + [str(y) for y in years])
if sel_year != "All":
    df_f = df[df["Year"] == int(sel_year)]
else:
    df_f = df

# ── PAGE 1: CITY LOOKUP ───────────────────────────────────────────────────────
if page == "🔍 City Lookup":
    st.title("City AQI Lookup")
    st.markdown("Find AQI and weather conditions for any city in any month.")

    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("Select City", sorted(df_f["City"].unique()))
    with col2:
        month_names = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]
        month_name = st.selectbox("Select Month", month_names)
        month_num  = month_names.index(month_name) + 1

    city_df = df_f[(df_f["City"] == city) & (df_f["Month"] == month_num)]

    if len(city_df) == 0:
        st.warning("No data found for this selection.")
    else:
        row = city_df.iloc[0] if len(city_df) == 1 else city_df.mean(numeric_only=True)
        aqi = int(row["AQI"])
        cat = aqi_category(aqi)
        col = aqi_color(aqi)

        st.markdown(f"""
        <div style="background:#1c2a1f;border:1px solid #2a4030;border-radius:16px;
                    padding:2rem;margin:1rem 0;display:flex;align-items:center;gap:2rem;">
          <div style="text-align:center;min-width:120px;">
            <div style="font-size:4rem;font-weight:800;color:{col};line-height:1;">{aqi}</div>
            <div style="font-size:0.7rem;color:#7aab82;text-transform:uppercase;letter-spacing:0.1em;">AQI</div>
          </div>
          <div>
            <div style="font-size:1.5rem;font-weight:700;">{city} · {month_name}</div>
            <div style="color:{col};font-size:1rem;margin:4px 0;">{cat}</div>
            <div style="color:#7aab82;font-size:0.9rem;">
              {"Excellent air — great for outdoor activities." if aqi<=50 else
               "Acceptable air quality for most people." if aqi<=100 else
               "Sensitive groups should limit outdoor activity." if aqi<=200 else
               "Everyone may experience health effects. Wear a mask." if aqi<=300 else
               "Health alert. Avoid outdoor activities." if aqi<=400 else
               "Emergency. Stay indoors with air purification."}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Weather stats
        c1, c2, c3, c4 = st.columns(4)
        weather_cols = {
            "Temp_C":        ("🌡️ Temperature", "°C"),
            "Humidity_pct":  ("💧 Humidity",    "%"),
            "Wind_kmh":      ("💨 Wind Speed",  "km/h"),
            "Rainfall_mm":   ("🌧️ Rainfall",    "mm"),
        }
        for (col_name, (label, unit)), col_widget in zip(weather_cols.items(), [c1,c2,c3,c4]):
            if col_name in row.index:
                col_widget.metric(label, f"{round(float(row[col_name]), 1)} {unit}")

        # Full year trend
        st.markdown("### AQI Trend — All 12 Months")
        city_all = df_f[df_f["City"] == city].groupby("Month")["AQI"].mean().reset_index()
        city_all = city_all.sort_values("Month")
        city_all["Color"] = city_all["AQI"].apply(aqi_color)
        city_all["Month_Name"] = city_all["Month"].apply(
            lambda m: ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"][m-1])

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=city_all["Month_Name"], y=city_all["AQI"],
            marker_color=city_all["Color"],
            name="AQI"
        ))
        fig.add_hline(y=200, line_dash="dash", line_color="#ff6d00",
                      annotation_text="Poor (200)")
        fig.add_hline(y=100, line_dash="dash", line_color="#ffd600",
                      annotation_text="Moderate (100)")
        fig.update_layout(
            plot_bgcolor="#111a14", paper_bgcolor="#111a14",
            font_color="#e8f5ea", height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="#1c2a1f"),
            yaxis=dict(gridcolor="#1c2a1f", title="AQI"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Pollutants
        if "PM2.5" in row.index:
            st.markdown("### Pollutant Levels")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("PM 2.5", f"{round(float(row.get('PM2.5',0)),1)} μg/m³")
            p2.metric("PM 10",  f"{round(float(row.get('PM10', 0)),1)} μg/m³")
            p3.metric("NO₂",   f"{round(float(row.get('NO2',  0)),1)} μg/m³")
            p4.metric("SO₂",   f"{round(float(row.get('SO2',  0)),1)} μg/m³")

# ── PAGE 2: CITY COMPARISON ───────────────────────────────────────────────────
elif page == "📊 City Comparison":
    st.title("City AQI Comparison")
    cities_sel = st.multiselect("Select cities to compare",
                                sorted(df_f["City"].unique()),
                                default=list(df_f["City"].unique())[:5])

    if cities_sel:
        cmp = df_f[df_f["City"].isin(cities_sel)].groupby(["City","Month"])["AQI"].mean().reset_index()
        cmp["Month_Name"] = cmp["Month"].apply(
            lambda m: ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"][m-1])

        fig = px.line(cmp, x="Month_Name", y="AQI", color="City",
                      category_orders={"Month_Name":
                          ["Jan","Feb","Mar","Apr","May","Jun",
                           "Jul","Aug","Sep","Oct","Nov","Dec"]})
        fig.update_layout(
            plot_bgcolor="#111a14", paper_bgcolor="#111a14",
            font_color="#e8f5ea", height=420,
            xaxis=dict(gridcolor="#1c2a1f"),
            yaxis=dict(gridcolor="#1c2a1f"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Ranking table
        st.markdown("### Annual Average AQI Ranking")
        rank = (df_f[df_f["City"].isin(cities_sel)]
                .groupby("City")["AQI"].mean()
                .sort_values(ascending=False)
                .reset_index())
        rank.columns = ["City", "Avg AQI"]
        rank["Avg AQI"] = rank["Avg AQI"].round(0).astype(int)
        rank["Category"] = rank["Avg AQI"].apply(aqi_category)
        rank["Rank"] = range(1, len(rank)+1)
        st.dataframe(rank[["Rank","City","Avg AQI","Category"]], use_container_width=True)

# ── PAGE 3: MONTHLY HEATMAP ───────────────────────────────────────────────────
elif page == "🗓️ Monthly Heatmap":
    st.title("Monthly AQI Heatmap")
    st.markdown("Each cell = average AQI for that city × month. Red = poor air quality.")

    pivot = df_f.groupby(["City","Month"])["AQI"].mean().reset_index()
    pivot["Month_Name"] = pivot["Month"].apply(
        lambda m: ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"][m-1])
    pivot_wide = pivot.pivot(index="City", columns="Month_Name", values="AQI")
    col_order = ["Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"]
    pivot_wide = pivot_wide.reindex(columns=[c for c in col_order if c in pivot_wide.columns])

    fig = px.imshow(pivot_wide,
                    color_continuous_scale=["#00e676","#ffd600","#ff6d00","#dd2c00","#aa00ff"],
                    aspect="auto",
                    labels=dict(color="AQI"))
    fig.update_layout(
        plot_bgcolor="#111a14", paper_bgcolor="#111a14",
        font_color="#e8f5ea", height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── PAGE 4: REGRESSION INSIGHTS ───────────────────────────────────────────────
elif page == "📈 Regression Insights":
    st.title("Regression & Correlation Insights")

    weather_vars = [c for c in ["Temp_C","Humidity_pct","Wind_kmh","Rainfall_mm"] if c in df_f.columns]

    if weather_vars:
        var = st.selectbox("Weather variable vs AQI", weather_vars,
                           format_func=lambda x: {
                               "Temp_C":"Temperature (°C)",
                               "Humidity_pct":"Humidity (%)",
                               "Wind_kmh":"Wind Speed (km/h)",
                               "Rainfall_mm":"Rainfall (mm)"
                           }.get(x, x))
        fig = px.scatter(df_f, x=var, y="AQI", color="Season",
                         trendline="ols",
                         opacity=0.6)
        fig.update_layout(
            plot_bgcolor="#111a14", paper_bgcolor="#111a14",
            font_color="#e8f5ea", height=420,
            xaxis=dict(gridcolor="#1c2a1f"),
            yaxis=dict(gridcolor="#1c2a1f"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Correlation table
        st.markdown("### Pearson Correlation with AQI")
        corr_vals = df_f[weather_vars + ["AQI"]].corr()["AQI"].drop("AQI").round(3)
        corr_df = corr_vals.reset_index()
        corr_df.columns = ["Variable", "Correlation with AQI"]
        corr_df["Direction"] = corr_df["Correlation with AQI"].apply(
            lambda v: "↑ AQI rises with this" if v > 0 else "↓ AQI falls with this")
        st.dataframe(corr_df, use_container_width=True)
    else:
        st.info("Weather columns not found. Run 01_data_cleaning.py first with weather data.")

# ── PAGE 5: OVERVIEW MAP ──────────────────────────────────────────────────────
elif page == "🗺️ Overview":
    st.title("India AQI Overview")

    # City coords
    COORDS = {
        "Delhi":       (28.6139, 77.2090), "Mumbai":    (19.0760, 72.8777),
        "Bangalore":   (12.9716, 77.5946), "Kolkata":   (22.5726, 88.3639),
        "Chennai":     (13.0827, 80.2707), "Hyderabad": (17.3850, 78.4867),
        "Ahmedabad":   (23.0225, 72.5714), "Lucknow":   (26.8467, 80.9462),
        "Patna":       (25.5941, 85.1376), "Pune":      (18.5204, 73.8567),
        "Jaipur":      (26.9124, 75.7873), "Chandigarh":(30.7333, 76.7794),
    }
    avg_aqi = df_f.groupby("City")["AQI"].mean().reset_index()
    avg_aqi["Lat"] = avg_aqi["City"].map(lambda c: COORDS.get(c, (0,0))[0])
    avg_aqi["Lon"] = avg_aqi["City"].map(lambda c: COORDS.get(c, (0,0))[1])
    avg_aqi["Category"] = avg_aqi["AQI"].apply(lambda v: aqi_category(v).split(" ")[0])
    avg_aqi = avg_aqi[(avg_aqi["Lat"] != 0)]

    fig = px.scatter_mapbox(avg_aqi,
        lat="Lat", lon="Lon", size="AQI",
        color="AQI",
        hover_name="City",
        hover_data={"AQI":True, "Category":True, "Lat":False, "Lon":False},
        color_continuous_scale=["#00e676","#ffd600","#ff6d00","#dd2c00","#aa00ff"],
        size_max=40,
        zoom=4.5,
        mapbox_style="carto-darkmatter",
        center={"lat":22.5,"lon":82.5},
        height=560
    )
    fig.update_layout(paper_bgcolor="#111a14", font_color="#e8f5ea",
                      margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities Tracked", df_f["City"].nunique())
    c2.metric("Overall Avg AQI", int(df_f["AQI"].mean()))
    c3.metric("Worst City", df_f.groupby("City")["AQI"].mean().idxmax())
    c4.metric("Best City",  df_f.groupby("City")["AQI"].mean().idxmin())
