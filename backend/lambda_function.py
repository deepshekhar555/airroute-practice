import json, os, time, math, urllib.request
import boto3

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
MODEL_ID = "us.amazon.nova-lite-v1:0"

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
ddb = boto3.resource("dynamodb", region_name="ap-south-1")
TABLE = ddb.Table("airroute-trips")

CACHE = {}
CACHE_TTL = 1800

MODE_FACTOR = {"walk":1.0,"cycle":1.8,"bus":0.9,"metro":0.6,"car":0.55}
SPEED = {"walk":5,"cycle":15,"bus":14,"metro":28,"car":20}
MODE_LABEL = {"walk":"walking","cycle":"cycling","bus":"bus or auto","metro":"the metro","car":"car"}

def fetch_openmeteo(lat, lon):
    url = (f"https://air-quality-api.open-meteo.com/v1/air-quality"
           f"?latitude={lat}&longitude={lon}"
           f"&hourly=pm2_5&forecast_days=3&timezone=Asia%2FKolkata")
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())

def hour_label(t):
    try:
        return t.split("T")[1][:5]
    except Exception:
        return t

def rule_advice(from_name, to_name, mode, traveller, minutes, best_h, worst_h, best_score, worst_score):
    """Deterministic natural-language advice. Used if Bedrock is unreachable."""
    bl = hour_label(best_h)
    wl = hour_label(worst_h)
    mode_text = MODE_LABEL.get(mode, mode)
    sensitive = traveller in ("child", "older", "asthma", "heart", "asthma_heart")
    bad_day = best_score > 90

    parts = [f"Leave at {bl}. Exposure is lowest then"]
    if best_score > 0:
        drop = max(0, int(round((worst_score - best_score) / max(worst_score,1) * 100)))
        if drop >= 5:
            parts.append(f"about {drop}% lower than the worst hour ({wl})")
    sentence = ", ".join(parts) + "."

    if sensitive:
        if bad_day:
            sentence += f" For a {traveller} traveller this is a bad-air day: keep outdoor time short and prefer the metro or a car with windows up over {mode_text}."
        else:
            sentence += f" For a {traveller} traveller, prefer the metro or a car with windows up over {mode_text}."
    elif bad_day:
        sentence += " It is a bad-air day, so keep outdoor time short if you can."

    return sentence

def ask_nova(from_name, to_name, mode, traveller, km, minutes, best_h, worst_h, best_score, worst_score):
    prompt = (
        f"You are AirRoute, a Delhi air-quality travel advisor. "
        f"Reply in 2 short sentences, under 55 words. Plain text only. No greetings, no markdown.\n\n"
        f"Trip: {from_name} to {to_name} by {mode}.\n"
        f"Traveller: {traveller}.\n"
        f"Distance: {km:.1f} km. Travel time: {minutes:.0f} min.\n"
        f"Best departure hour: {hour_label(best_h)} (score {best_score:.0f}).\n"
        f"Worst departure hour: {hour_label(worst_h)} (score {worst_score:.0f}).\n\n"
        f"Rules:\n"
        f"- Start with the action: 'Leave at <hour>.'\n"
        f"- Say the mode to use if the traveller is a child, older adult, or has asthma/heart condition.\n"
        f"- If best_score > 90, say it is a bad-air day and to avoid outdoor travel if possible."
    )
    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 200, "temperature": 0.7}
    )
    return resp["output"]["message"]["content"][0]["text"].strip()

def lambda_handler(event, context):
    p = event.get("queryStringParameters") or {}
    try:
        lat1 = float(p["lat1"]); lon1 = float(p["lon1"])
        lat2 = float(p["lat2"]); lon2 = float(p["lon2"])
    except (KeyError, ValueError, TypeError):
        return {"statusCode": 400, "body": json.dumps({"error": "bad coords"})}

    mode = p.get("mode", "walk")
    traveller = p.get("traveller", "adult")
    from_name = p.get("from_name", "start")
    to_name = p.get("to_name", "end")

    factor = MODE_FACTOR.get(mode, 1.0)
    speed = SPEED.get(mode, 5)

    key = f"{lat1:.4f},{lon1:.4f},{lat2:.4f},{lon2:.4f},{mode},{traveller}"
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < CACHE_TTL:
        print(json.dumps({"event": "cache_hit", "key": key}))
        return {"statusCode": 200, "body": json.dumps(CACHE[key][1])}

    try:
        a = fetch_openmeteo(lat1, lon1)
        b = fetch_openmeteo(lat2, lon2)
    except Exception as e:
        print(json.dumps({"event": "upstream_error", "err": str(e)}))
        return {"statusCode": 502, "body": json.dumps({"error": "forecast failed"})}

    times = a["hourly"]["time"]
    pm_start = a["hourly"]["pm2_5"]
    pm_end = b["hourly"]["pm2_5"]

    dx = (lon2 - lon1) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2))
    dy = (lat2 - lat1) * 111.0
    km = math.sqrt(dx*dx + dy*dy) * 1.3
    minutes = (km / speed) * 60.0

    scores = [((pm_start[i] + pm_end[i]) / 2.0) * minutes * factor for i in range(len(times))]
    best_i = min(range(len(scores)), key=lambda i: scores[i])
    worst_i = max(range(len(scores)), key=lambda i: scores[i])

    advice = None
    try:
        advice = ask_nova(from_name, to_name, mode, traveller, km, minutes,
                          times[best_i], times[worst_i], scores[best_i], scores[worst_i])
        print(json.dumps({"event": "nova_advice_ok"}))
    except Exception as e:
        print(json.dumps({"event": "nova_failed", "err": str(e)}))
        advice = rule_advice(from_name, to_name, mode, traveller, minutes,
                             times[best_i], times[worst_i], scores[best_i], scores[worst_i])
        print(json.dumps({"event": "rule_advice_used"}))

    result = {
        "time": times, "scores": scores, "o": pm_start, "d": pm_end,
        "best": hour_label(times[best_i]), "worst": hour_label(times[worst_i]),
        "best_full": times[best_i], "worst_full": times[worst_i],
        "best_score": round(scores[best_i], 2), "worst_score": round(scores[worst_i], 2),
        "km": round(km, 2), "minutes": round(minutes, 1),
        "advice": advice, "live": True
    }

    try:
        TABLE.put_item(Item={"id": key, "advice": advice, "best": times[best_i],
                             "traveller": traveller, "mode": mode, "ts": int(now)})
        print(json.dumps({"event": "trip_saved", "key": key}))
    except Exception as e:
        print(json.dumps({"event": "ddb_failed", "err": str(e)}))

    CACHE[key] = (now, result)
    return {"statusCode": 200, "body": json.dumps(result)}