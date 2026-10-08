import json

with open("model_params.json") as f:
    P = json.load(f)

def lambda_handler(event, context):
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    x = [float(body.get("day_num", 0)), float(body.get("pm25", 0)), float(body.get("pm10", 0))]
    y = P["intercept"] + sum(c * v for c, v in zip(P["coef"], x))
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"predicted_aqi": round(y, 2)})
    }
