# AQI & Weather Analysis — Indian Cities
## Complete Data Science Project

---

## Project Structure

```
aqi-project/
├── data/
│   └── 01_data_cleaning.py        ← Step 1: Clean & merge data
├── models/
│   └── 02_regression_models.py    ← Step 2: ML models & analysis
├── powerbi/
│   └── 03_powerbi_dax_measures.pq ← Step 3: Power BI setup
└── website/
    ├── index.html                 ← Static website (GitHub Pages)
    └── streamlit_app.py           ← Python web app (Streamlit)
```

---

## Step 1 — Get the Data

### Option A: Kaggle Dataset (Recommended — Free)
1. Go to: https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india
2. Download `city_day.csv` (26 cities, 2015–2020, daily AQI + pollutants)
3. Put it in the `data/` folder

### Option B: OpenWeatherMap API (for weather data)
1. Sign up at https://openweathermap.org/api (free tier)
2. Use the Historical Weather API to pull Temperature, Humidity, Wind, Rainfall
3. Match city + date to the AQI dataset

---

## Step 2 — Run Data Cleaning

```bash
cd data/
pip install pandas numpy openpyxl
python 01_data_cleaning.py
```

**Outputs:**
- `aqi_weather_daily.csv`   — daily rows
- `aqi_weather_monthly.csv` — city × month averages
- `aqi_weather_master.xlsx` — Excel with both sheets (for Power BI)

---

## Step 3 — Run Machine Learning Models

```bash
cd models/
pip install scikit-learn matplotlib seaborn xgboost joblib
python 02_regression_models.py
```

**Outputs:**
- `model_results.txt`         — all model performance metrics
- `feature_importance.csv/png` — what drives AQI
- `actual_vs_predicted.png`   — model accuracy chart
- `monthly_aqi_trend.png`     — seasonal pattern
- `city_aqi_ranking.csv`      — city ranking
- `aqi_model.pkl`             — saved model (use in web app)

---

## Step 4 — Power BI Dashboard

1. Open Power BI Desktop
2. Get Data → Excel → `aqi_weather_master.xlsx` → Monthly sheet
3. Open `03_powerbi_dax_measures.pq` and:
   - Paste the Power Query M code into Advanced Editor
   - Add each DAX measure in Modeling → New Measure
4. Build the 5 report pages as described in the file

**Pages to create:**
1. Overview Dashboard (India map + KPI cards)
2. City Deep Dive (trend + pollutant charts)
3. Monthly Heatmap (city × month matrix)
4. Regression Insights (scatter plots + feature importance)
5. Health Risk Tracker (gauges + category breakdown)

---

## Step 5 — Deploy the Website

### Option A: Static HTML (GitHub Pages — 0 cost)
1. Create a new GitHub repository
2. Upload `website/index.html`
3. Go to Settings → Pages → Branch: main → Folder: / (root)
4. Your site is live at: `https://yourusername.github.io/repo-name`

**Note:** The static site uses representative monthly averages.
To use your real data, replace `AQI_DATA` in the `<script>` section
with data exported from your cleaned CSV.

### Option B: Streamlit App (Interactive — recommended)
```bash
cd website/
pip install streamlit plotly pandas
streamlit run streamlit_app.py
```
- Copy `aqi_weather_monthly.csv` into the `website/` folder
- The app reads your real data automatically

**Deploy Streamlit to the web (free):**
1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect repo → select `website/streamlit_app.py`
4. Click Deploy — live in ~2 minutes

---

## Key Findings (Expected from Analysis)

| Finding | Expected Value |
|---------|---------------|
| Worst season | Winter (Dec–Feb), AQI 200–300+ |
| Best season | Monsoon (Jun–Sep), AQI 60–100 |
| Wind correlation | r ≈ −0.55 to −0.65 (negative) |
| Rainfall correlation | r ≈ −0.45 to −0.55 (negative) |
| Humidity correlation | r ≈ +0.40 to +0.50 (positive) |
| Best ML model | Random Forest or Gradient Boosting |
| Expected R² | 0.75 – 0.88 |
| Top pollutant | PM2.5 (most correlated with AQI) |
| Most polluted city | Delhi or Patna |
| Cleanest city | Shillong or Thiruvananthapuram |

---

## Technologies Used

| Tool | Purpose |
|------|---------|
| Python / Pandas | Data cleaning and feature engineering |
| scikit-learn | Linear regression, Random Forest, cross-validation |
| XGBoost | Gradient boosting model |
| Matplotlib / Seaborn | Charts and correlation heatmaps |
| Power BI + Power Query M | Interactive BI dashboard |
| DAX | Calculated measures (KPIs, rankings, YoY) |
| HTML / CSS / JavaScript | Static AQI lookup website |
| Streamlit + Plotly | Interactive Python web app |
| GitHub Pages | Free static site hosting |
| Streamlit Cloud | Free Python app hosting |

---

## Data Sources

- **CPCB India**: Central Pollution Control Board — official AQI source
- **Kaggle**: "Air Quality Data in India 2015–2020" (rohanrao)
  - URL: https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india
- **OpenWeatherMap**: Historical weather API (free tier, 1000 calls/day)
- **IMD**: India Meteorological Department (alternative weather source)

---

## AQI Categories (CPCB India Standard)

| AQI Range | Category | Health Impact |
|-----------|----------|---------------|
| 0–50 | Good | Minimal |
| 51–100 | Satisfactory | Minor breathing discomfort for sensitive people |
| 101–200 | Moderate | Breathing discomfort for asthma/heart patients |
| 201–300 | Poor | Breathing discomfort for most people on prolonged exposure |
| 301–400 | Very Poor | Respiratory illness on prolonged exposure |
| 401–500 | Severe | Serious respiratory effects, affects healthy people too |
