# Power BI — AQI & Weather Analysis
# Complete DAX Measures + Power Query M Code
# ============================================
# Paste each section into Power BI Desktop as instructed.
# Data source: aqi_weather_master.xlsx → Monthly sheet


# ════════════════════════════════════════════════════════════════════════════════
# POWER QUERY M CODE  (Home → Transform Data → Advanced Editor)
# ════════════════════════════════════════════════════════════════════════════════

# ── Step 1: Load Monthly Sheet ──────────────────────────────────────────────
# Paste this into Advanced Editor for the Monthly query:

let
    Source        = Excel.Workbook(File.Contents("C:\YourPath\aqi_weather_master.xlsx"), null, true),
    Monthly_Sheet = Source{[Item="Monthly",Kind="Sheet"]}[Data],
    Headers       = Table.PromoteHeaders(Monthly_Sheet, [PromoteAllScalars=true]),

    ChangedTypes  = Table.TransformColumnTypes(Headers, {
        {"City",         type text},
        {"Year",         Int64.Type},
        {"Month",        Int64.Type},
        {"Month_Name",   type text},
        {"Season",       type text},
        {"AQI",          type number},
        {"PM2.5",        type number},
        {"PM10",         type number},
        {"NO2",          type number},
        {"SO2",          type number},
        {"CO",           type number},
        {"O3",           type number},
        {"Temp_C",       type number},
        {"Humidity_pct", type number},
        {"Wind_kmh",     type number},
        {"Rainfall_mm",  type number},
        {"AQI_Category", type text},
        {"Health_Risk",  Int64.Type}
    }),

    # Add Date column (first day of each month — for time-series visuals)
    AddDate = Table.AddColumn(ChangedTypes, "Date",
        each #date([Year], [Month], 1), type date),

    # Month sort order (so months display Jan→Dec, not alphabetically)
    AddMonthSort = Table.AddColumn(AddDate, "Month_Sort",
        each [Month], Int64.Type),

    # AQI colour hex (for conditional formatting in Power BI)
    AddColour = Table.AddColumn(AddMonthSort, "AQI_Colour",
        each if [AQI] <= 50   then "#00b050"   // Good — Green
            else if [AQI] <= 100  then "#92d050"   // Satisfactory — Light Green
            else if [AQI] <= 200  then "#ffff00"   // Moderate — Yellow
            else if [AQI] <= 300  then "#ff9900"   // Poor — Orange
            else if [AQI] <= 400  then "#ff0000"   // Very Poor — Red
            else                       "#7030a0",  // Severe — Purple
        type text)

in AddColour


# ════════════════════════════════════════════════════════════════════════════════
# DAX MEASURES
# ════════════════════════════════════════════════════════════════════════════════
# In Power BI → Modeling → New Measure. Paste one at a time.

# ── KPI CARDS ────────────────────────────────────────────────────────────────

Avg AQI =
AVERAGE(Monthly[AQI])

Max AQI =
MAX(Monthly[AQI])

Min AQI =
MIN(Monthly[AQI])

Cities Tracked =
DISTINCTCOUNT(Monthly[City])

Months with Severe AQI =
CALCULATE(
    COUNTROWS(Monthly),
    Monthly[AQI_Category] = "Severe"
)

Pct Severe =
DIVIDE(
    CALCULATE(COUNTROWS(Monthly), Monthly[AQI_Category] = "Severe"),
    COUNTROWS(Monthly),
    0
)

# ── YEAR-OVER-YEAR ──────────────────────────────────────────────────────────

Avg AQI PY =
CALCULATE(
    [Avg AQI],
    SAMEPERIODLASTYEAR(Monthly[Date])
)

AQI YoY Change =
[Avg AQI] - [Avg AQI PY]

AQI YoY % =
DIVIDE([AQI YoY Change], [Avg AQI PY], BLANK())

# ── ROLLING AVERAGE (3-MONTH) ────────────────────────────────────────────────

AQI 3M Rolling Avg =
CALCULATE(
    [Avg AQI],
    DATESINPERIOD(Monthly[Date], LASTDATE(Monthly[Date]), -3, MONTH)
)

# ── RANKINGS ─────────────────────────────────────────────────────────────────

City AQI Rank =
RANKX(
    ALL(Monthly[City]),
    CALCULATE([Avg AQI]),
    ,
    DESC,
    DENSE
)

Best Month (Lowest AQI) =
CALCULATE(
    SELECTEDVALUE(Monthly[Month_Name]),
    TOPN(1, ALL(Monthly[Month_Name]), CALCULATE([Avg AQI]), ASC)
)

Worst Month (Highest AQI) =
CALCULATE(
    SELECTEDVALUE(Monthly[Month_Name]),
    TOPN(1, ALL(Monthly[Month_Name]), CALCULATE([Avg AQI]), DESC)
)

# ── WEATHER CORRELATIONS ─────────────────────────────────────────────────────

Avg Temperature =
AVERAGE(Monthly[Temp_C])

Avg Humidity =
AVERAGE(Monthly[Humidity_pct])

Avg Wind Speed =
AVERAGE(Monthly[Wind_kmh])

Total Rainfall =
SUM(Monthly[Rainfall_mm])

# AQI in High Wind months (wind > city median)
AQI in High Wind Months =
CALCULATE(
    [Avg AQI],
    Monthly[Wind_kmh] > CALCULATE(MEDIAN(Monthly[Wind_kmh]), ALL(Monthly))
)

AQI in Low Wind Months =
CALCULATE(
    [Avg AQI],
    Monthly[Wind_kmh] <= CALCULATE(MEDIAN(Monthly[Wind_kmh]), ALL(Monthly))
)

Wind Effect on AQI =
[AQI in Low Wind Months] - [AQI in High Wind Months]

# ── CATEGORY BREAKDOWN ───────────────────────────────────────────────────────

Pct Good =
DIVIDE(
    CALCULATE(COUNTROWS(Monthly), Monthly[AQI_Category] IN {"Good","Satisfactory"}),
    COUNTROWS(Monthly), 0
)

Pct Moderate =
DIVIDE(
    CALCULATE(COUNTROWS(Monthly), Monthly[AQI_Category] = "Moderate"),
    COUNTROWS(Monthly), 0
)

Pct Unhealthy =
DIVIDE(
    CALCULATE(COUNTROWS(Monthly), Monthly[AQI_Category] IN {"Poor","Very Poor","Severe"}),
    COUNTROWS(Monthly), 0
)

# ── PM2.5 vs PM10 ────────────────────────────────────────────────────────────

Avg PM2.5 =
AVERAGE(Monthly[PM2.5])

Avg PM10 =
AVERAGE(Monthly[PM10])

PM2.5 Share of PM10 =
DIVIDE([Avg PM2.5], [Avg PM10], 0)


# ════════════════════════════════════════════════════════════════════════════════
# REPORT PAGES SETUP GUIDE
# ════════════════════════════════════════════════════════════════════════════════

# PAGE 1 — OVERVIEW DASHBOARD
# ─────────────────────────────
# Visuals:
#   1. Map visual (Bing Maps) → Location: City, Bubble size: Avg AQI,
#      Bubble colour: AQI_Category (conditional: green→red scale)
#   2. Card  → [Avg AQI]
#   3. Card  → [Cities Tracked]
#   4. Card  → [Pct Severe] (format as %)
#   5. Donut chart → AQI_Category, Values: COUNTROWS
#   6. Bar chart → City (axis), Avg AQI (value), sorted DESC, top 10
#
# Slicers: City (dropdown, multi-select), Year, Season
# Theme colours: Green (#00b050) → Red (#ff0000) for AQI scale


# PAGE 2 — CITY DEEP DIVE
# ─────────────────────────
# Visuals:
#   1. Single-city slicer (required — drives all visuals)
#   2. Line chart → Month_Name (axis, sort by Month_Sort), Avg AQI
#   3. Clustered bar → Month_Name, PM2.5 and PM10 (clustered)
#   4. Scatter → X: Avg Temperature, Y: Avg AQI, size: Avg PM2.5
#   5. Scatter → X: Avg Wind Speed, Y: Avg AQI
#   6. KPI cards → [Best Month], [Worst Month], [City AQI Rank]


# PAGE 3 — MONTHLY SEASONALITY
# ──────────────────────────────
# Visuals:
#   1. Matrix visual → Rows: City, Cols: Month_Name (sorted),
#      Values: Avg AQI, Conditional formatting: background colour scale
#      (this creates the heatmap effect)
#   2. Bar chart → Month_Name, Avg AQI (all cities)
#   3. Line chart → Month (axis), multiple series: PM2.5, PM10, NO2
#   4. Bar chart → Season, Avg AQI


# PAGE 4 — REGRESSION INSIGHTS
# ──────────────────────────────
# Visuals:
#   1. Scatter → X: Avg Temperature, Y: Avg AQI,
#      Add trend line (Analytics pane → Trend Line)
#   2. Scatter → X: Avg Humidity, Y: Avg AQI, + trend line
#   3. Scatter → X: Avg Wind Speed, Y: Avg AQI, + trend line
#   4. Scatter → X: Total Rainfall, Y: Avg AQI, + trend line
#   5. Bar chart → import feature_importance.csv as separate table,
#      Feature (axis), Importance (value)
#   6. Card → [Wind Effect on AQI] (shows how much wind cleans air)


# PAGE 5 — HEALTH RISK TRACKER
# ──────────────────────────────
# Visuals:
#   1. Gauge → Avg AQI, min 0, max 500, target 100
#   2. Stacked bar → City, Good/Moderate/Unhealthy pct (100% stacked)
#   3. Table → City, Avg AQI, [City AQI Rank], Worst Month, AQI_Category
#   4. Line chart → Date (monthly), Avg AQI, add reference lines at 100, 200, 300


# ════════════════════════════════════════════════════════════════════════════════
# CONDITIONAL FORMATTING SETUP
# ════════════════════════════════════════════════════════════════════════════════

# For any AQI measure:
# Format → Conditional Formatting → Background Colour → Rules:
#   0  to  50  → #00b050  (Good, green)
#   51 to 100  → #92d050  (Satisfactory, light green)
#  101 to 200  → #ffff00  (Moderate, yellow)
#  201 to 300  → #ff9900  (Poor, orange)
#  301 to 400  → #ff0000  (Very Poor, red)
#  401+        → #7030a0  (Severe, purple)


# ════════════════════════════════════════════════════════════════════════════════
# CALCULATED COLUMNS (add in Data view, not Measures)
# ════════════════════════════════════════════════════════════════════════════════

Season Sort =
SWITCH(Monthly[Season],
    "Winter",       1,
    "Summer",       2,
    "Monsoon",      3,
    "Post-Monsoon", 4
)

AQI_Severity_Level =
SWITCH(Monthly[AQI_Category],
    "Good",         0,
    "Satisfactory", 1,
    "Moderate",     2,
    "Poor",         3,
    "Very Poor",    4,
    "Severe",       5
)
