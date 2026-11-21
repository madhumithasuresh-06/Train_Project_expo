import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

import joblib

DATA_DIR = "../data"
delay_df = pd.read_csv(f"{DATA_DIR}/delay_profile.csv")
trains_df = pd.read_csv(f"{DATA_DIR}/trains.csv")

# Merge to get train_type
df = pd.merge(delay_df, trains_df[['train_number', 'train_type']], on='train_number')

# Add synthetic features for SHAP to explain
np.random.seed(42)
seasons = ["Monsoon", "Summer", "Winter"]
weathers = ["Clear", "Heavy Rain", "Fog"]

# Let's expand the dataset to have these features
expanded_rows = []
for _, row in df.iterrows():
    base_delay = row['avg_delay_minutes']
    for _ in range(3):  # Create a few variations per train/day
        season = np.random.choice(seasons)
        weather = np.random.choice(weathers)

        delay = base_delay
        if season == "Monsoon":
            delay += 10
        if weather == "Heavy Rain":
            delay += 15
        if weather == "Fog":
            delay += 8
        if row['day_of_week'] in ["Sat", "Sun"]:
            delay += 5
        if row['train_type'] == "passenger":
            delay += 5

        expanded_rows.append({
            "train_number": row['train_number'],
            "day_of_week": row['day_of_week'],
            "train_type": row['train_type'],
            "season": season,
            "weather": weather,
            "delay": delay
        })

ml_df = pd.DataFrame(expanded_rows)
feature_columns = ["day_of_week", "train_type", "season", "weather"]
target_column = "delay"

# Split the available dataset into train and test sets before fitting any preprocessing
# so the model is evaluated on unseen data and there is no data leakage.
X = ml_df[feature_columns]
y = ml_df[target_column]
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
)

# Reuse the existing LabelEncoder preprocessing, but fit it only on the training data.
# This preserves the project's encoding structure while avoiding leakage from the test set.
le_day = LabelEncoder()
le_type = LabelEncoder()
le_season = LabelEncoder()
le_weather = LabelEncoder()

X_train_encoded = pd.DataFrame({
    'day_of_week': le_day.fit_transform(X_train['day_of_week']),
    'train_type': le_type.fit_transform(X_train['train_type']),
    'season': le_season.fit_transform(X_train['season']),
    'weather': le_weather.fit_transform(X_train['weather']),
})

X_test_encoded = pd.DataFrame({
    'day_of_week': le_day.transform(X_test['day_of_week']),
    'train_type': le_type.transform(X_test['train_type']),
    'season': le_season.transform(X_test['season']),
    'weather': le_weather.transform(X_test['weather']),
})

print("Training Random Forest Regressor...")
model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
model.fit(X_train_encoded, y_train)

# Evaluation section: measure how well the existing Random Forest regressor performs on
# the held-out test set using regression metrics that are calculated from the actual test data.
y_pred = model.predict(X_test_encoded)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\nMODEL PERFORMANCE")
print("-----------------")
print(f"MAE  : {mae:.2f} minutes")
print(f"RMSE : {rmse:.2f} minutes")
print(f"R²   : {r2:.2f}")

metrics = {
    "MAE": round(float(mae), 2),
    "RMSE": round(float(rmse), 2),
    "R2": round(float(r2), 2),
}

with open("model_metrics.json", "w", encoding="utf-8") as metrics_file:
    json.dump(metrics, metrics_file, indent=4)

print("\nMetrics saved to model_metrics.json")

# Save models and encoders
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/rf_model.joblib")
joblib.dump(le_day, "models/le_day.joblib")
joblib.dump(le_type, "models/le_type.joblib")
joblib.dump(le_season, "models/le_season.joblib")
joblib.dump(le_weather, "models/le_weather.joblib")

# Save a lookup for train_number to train_type
train_types = trains_df.set_index('train_number')['train_type'].to_dict()
joblib.dump(train_types, "models/train_types.joblib")

print("Model trained and saved in models/")
