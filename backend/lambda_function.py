import joblib
import json

model = joblib.load("aqi_model.pkl")

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    day_num = body.get("day_num", 0)
    pm25 = body.get("pm25", 0)
    pm10 = body.get("pm10", 0)
    
    prediction = model.predict([[day_num, pm25, pm10]])
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"predicted_aqi": round(float(prediction[0]), 2)})
    }
