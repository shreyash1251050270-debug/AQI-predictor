"""
AQI & Weather Data Cleaning Pipeline
=====================================
Run this FIRST before any analysis.

Inputs  : city_day.csv  (Kaggle: Air Quality Data in India 2015-2020)
          weather_raw.csv (OpenWeatherMap / IMD export)
Output  : aqi_weather_merged.csv  (clean, analysis-ready)

Install : pip install pandas numpy openpyxl requests
"""

import pandas as pd
import numpy as np

# ── 1. LOAD RAW DATA ─────────────────────────────────────────────────────────

def load_aqi(path="city_day.csv"):
    df = pd.read_csv(path, parse_dates=["Date"])
    print(f"[AQI]  Loaded {len(df):,} rows, {df['City'].nunique()} cities")
    return df

def load_weather(path="weather_raw.csv"):
    df = pd.read_csv(path, parse_dates=["Date"])
    print(f"[Weather] Loaded {len(df):,} rows")
    return df

# ── 2. CITY NAME NORMALISATION ───────────────────────────────────────────────

CITY_MAP = {
    "Bengaluru"          : "Bangalore",
    "Gurugram"           : "Gurgaon",
    "Navi Mumbai"        : "Mumbai",
    "Greater Mumbai"     : "Mumbai",
    "Thiruvananthapuram" : "Trivandrum",
    "Vishakhapatnam"     : "Visakhapatnam",
    "Bhopal "            : "Bhopal",      # trailing space
    "delhi"              : "Delhi",       # lowercase variant
}

def normalise_cities(df, col="City"):
    df[col] = df[col].str.strip()
    df[col] = df[col].replace(CITY_MAP)
    return df

# ── 3. AQI CLEANING ──────────────────────────────────────────────────────────

POLLUTANTS = ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3",
              "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene"]

def clean_aqi(df):
    # Keep only rows with AQI
    df = df.dropna(subset=["AQI"])

    # Clip physical impossibilities
    df["PM2.5"] = df["PM2.5"].clip(lower=0, upper=1000)
    df["PM10"]  = df["PM10"].clip(lower=0, upper=1500)
    df["AQI"]   = df["AQI"].clip(lower=0, upper=999)

    # Fill pollutant nulls with city-month median (not 0)
    for col in POLLUTANTS:
        if col in df.columns:
            df[col] = df.groupby(["City", df["Date"].dt.month])[col] \
                        .transform(lambda x: x.fillna(x.median()))

    # Remove duplicates
    df = df.drop_duplicates(subset=["City", "Date"])
    print(f"[AQI]  After cleaning: {len(df):,} rows")
    return df

# ── 4. WEATHER CLEANING ───────────────────────────────────────────────────────

def clean_weather(df):
    # Expected columns: City, Date, Temp_C, Humidity_pct, Wind_kmh, Rainfall_mm
    rename = {
        "temperature" : "Temp_C",
        "humidity"    : "Humidity_pct",
        "wind_speed"  : "Wind_kmh",
        "rainfall"    : "Rainfall_mm",
        "city"        : "City",
        "date"        : "Date",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Fill missing rainfall with 0 (no data = no rain reported)
    if "Rainfall_mm" in df.columns:
        df["Rainfall_mm"] = df["Rainfall_mm"].fillna(0)

    # Clip temperature to India's realistic range
    if "Temp_C" in df.columns:
        df["Temp_C"] = df["Temp_C"].clip(-5, 55)

    df = df.drop_duplicates(subset=["City", "Date"])
    print(f"[Weather] After cleaning: {len(df):,} rows")
    return df

# ── 5. MERGE ──────────────────────────────────────────────────────────────────

def merge_datasets(aqi_df, weather_df):
    merged = pd.merge(aqi_df, weather_df, on=["City", "Date"], how="left")
    print(f"[Merge] {len(merged):,} rows after join")
    return merged

# ── 6. FEATURE ENGINEERING ────────────────────────────────────────────────────

def add_features(df):
    df["Year"]    = df["Date"].dt.year
    df["Month"]   = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%B")
    df["Quarter"] = df["Date"].dt.quarter
    df["DayOfYear"] = df["Date"].dt.dayofyear

    # Season (India-specific)
    season_map = {
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Summer",  4: "Summer", 5: "Summer",
        6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
        10: "Post-Monsoon", 11: "Post-Monsoon"
    }
    df["Season"] = df["Month"].map(season_map)

    # AQI Category (CPCB India standard)
    def aqi_category(val):
        if val <= 50:   return "Good"
        if val <= 100:  return "Satisfactory"
        if val <= 200:  return "Moderate"
        if val <= 300:  return "Poor"
        if val <= 400:  return "Very Poor"
        return "Severe"

    df["AQI_Category"] = df["AQI"].apply(aqi_category)

    # Health Risk Score (0-5 for easy colour coding)
    cat_score = {
        "Good": 0, "Satisfactory": 1, "Moderate": 2,
        "Poor": 3, "Very Poor": 4, "Severe": 5
    }
    df["Health_Risk"] = df["AQI_Category"].map(cat_score)

    # Pollution index (composite)
    if "PM2.5" in df.columns and "PM10" in df.columns:
        df["Pollution_Index"] = (
            df["PM2.5"].fillna(0) * 0.5 +
            df["PM10"].fillna(0)  * 0.3 +
            df["NO2"].fillna(0)   * 0.2
        ).round(2)

    return df

# ── 7. MONTHLY AGGREGATE ──────────────────────────────────────────────────────

def create_monthly_summary(df):
    """
    Creates city-month pivot — the main table for Power BI & website.
    """
    agg = {
        "AQI"          : "mean",
        "PM2.5"        : "mean",
        "PM10"         : "mean",
        "NO2"          : "mean",
        "SO2"          : "mean",
        "CO"           : "mean",
        "O3"           : "mean",
        "Temp_C"       : "mean",
        "Humidity_pct" : "mean",
        "Wind_kmh"     : "mean",
        "Rainfall_mm"  : "sum",
        "Health_Risk"  : "max",   # worst day in month
    }
    # Keep only columns that exist
    agg = {k: v for k, v in agg.items() if k in df.columns}

    monthly = (
        df.groupby(["City", "Year", "Month", "Month_Name", "Season"])
          .agg(agg)
          .reset_index()
    )
    monthly = monthly.round(2)

    # Re-derive AQI category on monthly mean
    def aqi_category(val):
        if val <= 50:   return "Good"
        if val <= 100:  return "Satisfactory"
        if val <= 200:  return "Moderate"
        if val <= 300:  return "Poor"
        if val <= 400:  return "Very Poor"
        return "Severe"

    monthly["AQI_Category"] = monthly["AQI"].apply(aqi_category)
    print(f"[Monthly] {len(monthly):,} city-month rows created")
    return monthly

# ── 8. EXPORT ─────────────────────────────────────────────────────────────────

def export(daily_df, monthly_df):
    daily_df.to_csv("aqi_weather_daily.csv", index=False)
    monthly_df.to_csv("aqi_weather_monthly.csv", index=False)

    # Excel with two sheets (for Power BI)
    with pd.ExcelWriter("aqi_weather_master.xlsx", engine="openpyxl") as w:
        daily_df.to_excel(w, sheet_name="Daily", index=False)
        monthly_df.to_excel(w, sheet_name="Monthly", index=False)

    print("\n✅ Exported:")
    print("   aqi_weather_daily.csv")
    print("   aqi_weather_monthly.csv")
    print("   aqi_weather_master.xlsx  (use this in Power BI)")

# ── 9. QUICK VALIDATION REPORT ────────────────────────────────────────────────

def validation_report(df):
    print("\n── Validation Report ──────────────────────────────")
    print(f"Cities       : {sorted(df['City'].unique())}")
    print(f"Date range   : {df['Date'].min().date()} → {df['Date'].max().date()}")
    print(f"Rows         : {len(df):,}")
    print(f"AQI nulls    : {df['AQI'].isna().sum()}")
    print(f"AQI range    : {df['AQI'].min():.0f} – {df['AQI'].max():.0f}")
    print(f"Category mix :")
    print(df["AQI_Category"].value_counts().to_string())
    print("────────────────────────────────────────────────────\n")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── OPTION A: You have both AQI + weather CSVs ──
    # aqi_raw     = load_aqi("city_day.csv")
    # weather_raw = load_weather("weather_raw.csv")
    # aqi_clean   = clean_aqi(normalise_cities(aqi_raw))
    # wth_clean   = clean_weather(normalise_cities(weather_raw))
    # daily       = merge_datasets(aqi_clean, wth_clean)

    # ── OPTION B: AQI only (weather columns already in Kaggle CSV) ──
    aqi_raw   = load_aqi("city_day.csv")
    aqi_clean = clean_aqi(normalise_cities(aqi_raw))
    daily     = add_features(aqi_clean)

    validation_report(daily)
    monthly = create_monthly_summary(daily)
    export(daily, monthly)
