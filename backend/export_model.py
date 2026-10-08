import joblib, json
model = joblib.load("../models/aqi_model.pkl")
params = {
    "features": ["day_num", "PM2.5", "PM10"],
    "coef": [float(c) for c in model.coef_],
    "intercept": float(model.intercept_),
}
json.dump(params, open("package/model_params.json", "w"))
print(params)
