import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import numpy as np

# Load cleaned Delhi data
df = pd.read_csv("../data/delhi_aqi_clean.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.dropna(subset=["AQI"])
df = df.sort_values("Date").reset_index(drop=True)

# Create a simple time-based feature: day number since start
df["day_num"] = (df["Date"] - df["Date"].min()).dt.days

# Use day_num and PM2.5/PM10 as features to predict AQI
features = ["day_num", "PM2.5", "PM10"]
df_model = df.dropna(subset=features)

X = df_model[features]
y = df_model["AQI"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)
mae = mean_absolute_error(y_test, predictions)

print("Model trained successfully.")
print("Mean Absolute Error:", round(mae, 2))
print("\nSample predictions vs actual:")
for i in range(5):
    print(f"Predicted: {predictions[i]:.1f}, Actual: {y_test.values[i]:.1f}")

import joblib
joblib.dump(model, "../models/aqi_model.pkl")
print("\nModel saved to models/aqi_model.pkl")
