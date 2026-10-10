"""AirRoute forecast API (AWS Lambda, Function URL).

GET ?lat1=..&lon1=..&lat2=..&lon2=.. returns hourly PM2.5 for both points:
{"time": [...], "o": [...], "d": [...], "live": true}
Source: Open-Meteo air quality forecast (CAMS model). Results are cached in the
warm Lambda container for 30 minutes and every request is logged to CloudWatch.
"""
import json
import time
import urllib.request

CACHE = {}
TTL = 1800


def _resp(code, body):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    q = event.get("queryStringParameters") or {}
    try:
        a = (float(q["lat1"]), float(q["lon1"]))
        b = (float(q["lat2"]), float(q["lon2"]))
    except (KeyError, ValueError):
        return _resp(400, {"error": "lat1, lon1, lat2 and lon2 are required numbers"})

    # Keep requests inside India so the endpoint cannot be used as a generic proxy.
    if not all(6 <= p[0] <= 37 and 68 <= p[1] <= 98 for p in (a, b)):
        return _resp(400, {"error": "coordinates must be inside India"})

    key = tuple(round(v, 3) for v in (*a, *b))
    hit = CACHE.get(key)
    if hit and time.time() - hit[0] < TTL:
        print(json.dumps({"event": "cache_hit", "from": a, "to": b}))
        return _resp(200, hit[1])

    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        "?latitude=%s,%s&longitude=%s,%s&hourly=pm2_5"
        "&forecast_days=3&timezone=Asia%%2FKolkata" % (a[0], b[0], a[1], b[1])
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)
        arr = data if isinstance(data, list) else [data]
        if len(arr) < 2:
            arr.append(arr[0])
        out = {
            "time": arr[0]["hourly"]["time"],
            "o": arr[0]["hourly"]["pm2_5"],
            "d": arr[1]["hourly"]["pm2_5"],
            "live": True,
        }
    except Exception as exc:  # network error, bad payload, upstream outage
        print(json.dumps({"event": "upstream_error", "error": str(exc)}))
        return _resp(502, {"error": "forecast service unavailable"})

    CACHE[key] = (time.time(), out)
    print(json.dumps({"event": "forecast_fetched", "from": a, "to": b}))
    return _resp(200, out)