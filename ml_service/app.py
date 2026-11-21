from fastapi import FastAPI
import joblib
import pandas as pd
import numpy as np
import shap
import uvicorn
import random
import os

app = FastAPI()

# Load artifacts
model = joblib.load("models/rf_model.joblib")
le_day = joblib.load("models/le_day.joblib")
le_type = joblib.load("models/le_type.joblib")
le_season = joblib.load("models/le_season.joblib")
le_weather = joblib.load("models/le_weather.joblib")
train_types = joblib.load("models/train_types.joblib")

# Create SHAP explainer
explainer = shap.TreeExplainer(model)

# Friendly name mapping
FRIENDLY_NAMES = {
    "day_of_week": "Day of week congestion",
    "train_type": "Train priority class",
    "season": "Seasonal conditions",
    "weather": "Weather conditions"
}

def get_friendly_value(feature, val_idx):
    if feature == "season": return le_season.inverse_transform([val_idx])[0]
    if feature == "weather": return le_weather.inverse_transform([val_idx])[0]
    if feature == "day_of_week": return le_day.inverse_transform([val_idx])[0]
    if feature == "train_type": return le_type.inverse_transform([val_idx])[0]
    return str(val_idx)

@app.get("/predict")
def predict_delay(train_number: int, day: str):
    t_type = train_types.get(train_number, "express")
    
    # Simulate current condition randomly for the API call to show variation
    season = random.choice(["Monsoon", "Summer", "Winter"])
    weather = random.choice(["Clear", "Heavy Rain", "Fog"])
    
    try:
        d_idx = le_day.transform([day])[0]
    except:
        d_idx = le_day.transform(["Mon"])[0] # Fallback
        
    t_idx = le_type.transform([t_type])[0]
    s_idx = le_season.transform([season])[0]
    w_idx = le_weather.transform([weather])[0]
    
    X_input = pd.DataFrame([[d_idx, t_idx, s_idx, w_idx]], columns=["day_of_week", "train_type", "season", "weather"])
    
    # Predict
    pred = model.predict(X_input)[0]
    
    # SHAP
    shap_values = explainer.shap_values(X_input)[0]
    
    explanations = []
    
    # Map top contributors
    for i, col in enumerate(X_input.columns):
        val = shap_values[i]
        if abs(val) > 1.0: # Only significant impacts
            impact_str = f"+{int(val)} min" if val > 0 else f"{int(val)} min"
            friendly_val = get_friendly_value(col, X_input.iloc[0, i])
            
            # Format friendly string
            if col == "weather" and friendly_val != "Clear":
                feat_str = f"{friendly_val} weather delays"
            elif col == "season" and friendly_val == "Monsoon":
                feat_str = "Monsoon season congestion"
            elif col == "day_of_week" and friendly_val in ["Sat", "Sun"]:
                feat_str = f"Weekend ({friendly_val}) high traffic"
            elif col == "day_of_week":
                feat_str = f"Weekday ({friendly_val}) normal traffic"
            elif col == "train_type":
                feat_str = f"{friendly_val.title()} train priority routing"
            else:
                feat_str = f"{FRIENDLY_NAMES[col]} ({friendly_val})"
                
            explanations.append({
                "feature": feat_str,
                "impact": impact_str,
                "raw_value": val
            })
            
    # Sort by absolute impact
    explanations.sort(key=lambda x: abs(x["raw_value"]), reverse=True)
    
    return {
        "train_number": train_number,
        "day": day,
        "predicted_delay_minutes": int(pred),
        "explanations": [{"feature": x["feature"], "impact": x["impact"]} for x in explanations]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
