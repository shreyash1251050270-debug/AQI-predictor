"""
AQI Regression & Machine Learning Models
==========================================
Run AFTER 01_data_cleaning.py

Input  : aqi_weather_monthly.csv
Outputs: model_results.txt
         feature_importance.csv
         predictions.csv
         aqi_model.pkl  (saved model for website)

Install: pip install pandas numpy scikit-learn matplotlib seaborn xgboost joblib
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
import joblib

# ── 1. LOAD DATA ──────────────────────────────────────────────────────────────

def load_data():
    df = pd.read_csv("aqi_weather_monthly.csv")
    print(f"Loaded {len(df):,} rows, columns: {list(df.columns)}")
    return df

# ── 2. FEATURE SELECTION ──────────────────────────────────────────────────────

WEATHER_FEATURES = ["Temp_C", "Humidity_pct", "Wind_kmh", "Rainfall_mm"]
TIME_FEATURES    = ["Month", "Quarter"]
CITY_FEATURE     = ["City"]
TARGET           = "AQI"

def prepare_features(df):
    features = WEATHER_FEATURES + TIME_FEATURES + CITY_FEATURE
    available = [f for f in features if f in df.columns]

    data = df[available + [TARGET]].dropna()

    # Encode City as a label integer
    le = LabelEncoder()
    data["City_encoded"] = le.fit_transform(data["City"])

    feature_cols = [f for f in available if f != "City"] + ["City_encoded"]
    X = data[feature_cols]
    y = data[TARGET]

    print(f"Features used : {feature_cols}")
    print(f"Samples       : {len(X):,}")
    return X, y, le, feature_cols

# ── 3. CORRELATION ANALYSIS ───────────────────────────────────────────────────

def correlation_analysis(df):
    numeric_cols = WEATHER_FEATURES + [TARGET]
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    corr = df[numeric_cols].corr()

    print("\n── Pearson Correlations with AQI ──────────────────")
    aqi_corr = corr[TARGET].drop(TARGET).sort_values()
    for var, val in aqi_corr.items():
        direction = "↑ AQI rises" if val > 0 else "↓ AQI falls"
        print(f"  {var:20s}  r = {val:+.3f}  →  as {var} increases, {direction}")
    print("────────────────────────────────────────────────────\n")

    # Save heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn_r",
                center=0, linewidths=0.5)
    plt.title("AQI & Weather Variable Correlations")
    plt.tight_layout()
    plt.savefig("correlation_heatmap.png", dpi=150)
    plt.close()
    print("Saved: correlation_heatmap.png")
    return corr

# ── 4. TRAIN/TEST SPLIT ───────────────────────────────────────────────────────

def split(X, y, test_size=0.2, seed=42):
    return train_test_split(X, y, test_size=test_size, random_state=seed)

# ── 5. MODEL DEFINITIONS ──────────────────────────────────────────────────────

MODELS = {
    "Linear Regression"     : LinearRegression(),
    "Ridge Regression"      : Ridge(alpha=10),
    "Lasso Regression"      : Lasso(alpha=1),
    "Random Forest"         : RandomForestRegressor(n_estimators=200, max_depth=8,
                                                     random_state=42, n_jobs=-1),
    "Gradient Boosting"     : GradientBoostingRegressor(n_estimators=200,
                                                         learning_rate=0.05,
                                                         max_depth=5, random_state=42),
}

# ── 6. EVALUATE ALL MODELS ────────────────────────────────────────────────────

def evaluate_models(X_train, X_test, y_train, y_test):
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    results = []
    trained_models = {}

    for name, model in MODELS.items():
        model.fit(X_train_sc, y_train)
        y_pred = model.predict(X_test_sc)

        mae  = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2   = r2_score(y_test, y_pred)

        # 5-fold CV R²
        cv_scores = cross_val_score(model, X_train_sc, y_train,
                                    cv=KFold(5, shuffle=True, random_state=42),
                                    scoring="r2")

        results.append({
            "Model"    : name,
            "MAE"      : round(mae, 2),
            "RMSE"     : round(rmse, 2),
            "R2"       : round(r2, 4),
            "CV_R2_mean": round(cv_scores.mean(), 4),
            "CV_R2_std" : round(cv_scores.std(), 4),
        })
        trained_models[name] = (model, y_pred)
        print(f"  {name:28s}  MAE={mae:.1f}  RMSE={rmse:.1f}  R²={r2:.4f}  CV-R²={cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    results_df = pd.DataFrame(results).sort_values("R2", ascending=False)
    return results_df, trained_models, scaler

# ── 7. FEATURE IMPORTANCE ─────────────────────────────────────────────────────

def feature_importance(model, feature_names, model_name="Random Forest"):
    if hasattr(model, "feature_importances_"):
        imp = pd.Series(model.feature_importances_, index=feature_names)
        imp = imp.sort_values(ascending=False)

        plt.figure(figsize=(8, 5))
        imp.plot(kind="bar", color="#1D9E75", edgecolor="white")
        plt.title(f"Feature Importance — {model_name}")
        plt.xlabel("Feature")
        plt.ylabel("Importance")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig("feature_importance.png", dpi=150)
        plt.close()

        imp.to_csv("feature_importance.csv", header=["Importance"])
        print("\nTop features driving AQI:")
        for feat, val in imp.items():
            print(f"  {feat:20s}  {val:.4f}  {'█' * int(val * 60)}")
        print("Saved: feature_importance.png, feature_importance.csv")
        return imp
    else:
        print(f"{model_name} has no feature_importances_ attribute")
        return None

# ── 8. ACTUAL vs PREDICTED PLOT ───────────────────────────────────────────────

def plot_actual_vs_predicted(y_test, y_pred, model_name="Best Model"):
    plt.figure(figsize=(7, 7))
    plt.scatter(y_test, y_pred, alpha=0.4, color="#378ADD", edgecolors="none", s=30)
    lim = (min(y_test.min(), y_pred.min()) - 10,
           max(y_test.max(), y_pred.max()) + 10)
    plt.plot(lim, lim, "r--", linewidth=1.5, label="Perfect prediction")
    plt.xlabel("Actual AQI")
    plt.ylabel("Predicted AQI")
    plt.title(f"Actual vs Predicted AQI — {model_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig("actual_vs_predicted.png", dpi=150)
    plt.close()
    print("Saved: actual_vs_predicted.png")

# ── 9. MONTHLY TREND PLOT ─────────────────────────────────────────────────────

def plot_monthly_trend(df):
    if "Month" not in df.columns or "AQI" not in df.columns:
        return
    monthly_aqi = df.groupby("Month")["AQI"].mean()
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]

    plt.figure(figsize=(10, 5))
    bars = plt.bar(range(1, 13), monthly_aqi.reindex(range(1, 13)),
                   color=["#E24B4A" if v > 200 else "#EF9F27" if v > 100
                          else "#1D9E75" for v in monthly_aqi.reindex(range(1, 13)).fillna(0)])
    plt.xticks(range(1, 13), month_names)
    plt.xlabel("Month")
    plt.ylabel("Average AQI")
    plt.title("Average AQI by Month (All Cities)")
    plt.axhline(200, color="#E24B4A", linestyle="--", linewidth=1, label="Poor threshold (200)")
    plt.axhline(100, color="#EF9F27", linestyle="--", linewidth=1, label="Moderate threshold (100)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("monthly_aqi_trend.png", dpi=150)
    plt.close()
    print("Saved: monthly_aqi_trend.png")

# ── 10. CITY RANKING ──────────────────────────────────────────────────────────

def city_ranking(df):
    if "City" not in df.columns:
        return
    ranking = df.groupby("City")["AQI"].mean().sort_values(ascending=False)
    print("\n── City AQI Ranking (worst → best) ───────────────")
    for i, (city, aqi) in enumerate(ranking.items(), 1):
        bar = "█" * int(aqi / 10)
        print(f"  {i:2d}. {city:20s}  {aqi:5.0f}  {bar}")
    ranking.to_csv("city_aqi_ranking.csv", header=["Mean_AQI"])
    print("Saved: city_aqi_ranking.csv\n")
    return ranking

# ── 11. SAVE BEST MODEL ───────────────────────────────────────────────────────

def save_best_model(results_df, trained_models, scaler, feature_cols):
    best_name = results_df.iloc[0]["Model"]
    best_model, _ = trained_models[best_name]
    joblib.dump({"model": best_model, "scaler": scaler, "features": feature_cols},
                "aqi_model.pkl")
    print(f"\n✅ Best model saved: {best_name}  →  aqi_model.pkl")
    return best_name, best_model

# ── 12. GENERATE RESULTS REPORT ───────────────────────────────────────────────

def save_report(results_df, corr, best_name):
    with open("model_results.txt", "w") as f:
        f.write("AQI & Weather Analysis — Model Results\n")
        f.write("=" * 50 + "\n\n")
        f.write("Model Performance Comparison\n")
        f.write(results_df.to_string(index=False))
        f.write(f"\n\nBest Model: {best_name}\n\n")
        f.write("Correlations with AQI\n")
        f.write("-" * 30 + "\n")
        if "AQI" in corr.columns:
            f.write(corr["AQI"].drop("AQI").sort_values().to_string())
    print("Saved: model_results.txt")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = load_data()

    print("\n[1/6] Correlation analysis ...")
    corr = correlation_analysis(df)

    print("[2/6] Preparing features ...")
    X, y, le, feature_cols = prepare_features(df)
    X_train, X_test, y_train, y_test = split(X, y)

    print(f"[3/6] Training {len(MODELS)} models ...")
    results_df, trained_models, scaler = evaluate_models(X_train, X_test, y_train, y_test)

    print("\nModel Rankings:")
    print(results_df.to_string(index=False))

    print("\n[4/6] Feature importance ...")
    rf_model, rf_pred = trained_models["Random Forest"]
    feature_importance(rf_model, feature_cols)

    print("[5/6] Visualisations ...")
    best_name = results_df.iloc[0]["Model"]
    _, best_pred = trained_models[best_name]
    plot_actual_vs_predicted(y_test, best_pred, best_name)
    plot_monthly_trend(df)
    city_ranking(df)

    # Save predictions
    pred_df = X_test.copy()
    pred_df["Actual_AQI"]    = y_test.values
    pred_df["Predicted_AQI"] = best_pred.round(0)
    pred_df["Error"]         = (pred_df["Actual_AQI"] - pred_df["Predicted_AQI"]).abs()
    pred_df.to_csv("predictions.csv", index=False)

    print("[6/6] Saving best model ...")
    save_best_model(results_df, trained_models, scaler, feature_cols)
    save_report(results_df, corr, best_name)

    print("\n── All outputs ─────────────────────────────────────")
    print("  correlation_heatmap.png")
    print("  feature_importance.png / .csv")
    print("  actual_vs_predicted.png")
    print("  monthly_aqi_trend.png")
    print("  city_aqi_ranking.csv")
    print("  predictions.csv")
    print("  aqi_model.pkl")
    print("  model_results.txt")
    print("────────────────────────────────────────────────────")
