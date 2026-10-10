"""AirRoute environmental AQI prediction API and static dashboard server."""

from __future__ import annotations

import json
import math
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
MODEL_PARAMS = BACKEND_DIR / "package" / "model_params.json"
FRONTEND_DIR = ROOT_DIR / "frontend"


def _load_model_params() -> dict[str, Any]:
    with MODEL_PARAMS.open(encoding="utf-8") as handle:
        return json.load(handle)


MODEL_PARAMS_DATA = _load_model_params()

PROJECTS = [
    {
        "name": "Suraksha",
        "subtitle": "An Agentic Companion for an aging parent",
        "recognition": "First Commit winner",
        "team": "STARBUGS",
        "project_type": "AI companion",
        "source": "First Commit official project showcase",
        "media_type": "project",
        "media_url": "https://github.com/harshendram/firstcommit-hack",
        "media_label": "Explore the project",
    },
    {
        "name": "Beacon Night Shift",
        "subtitle": "The on-call agent that fixes the 3 AM page with your voice",
        "recognition": "First Commit winner",
        "team": "COFFEANDCODE",
        "project_type": "Voice agent",
        "source": "First Commit official project showcase",
        "media_type": "video",
        "media_url": "https://youtu.be/a3SxZHvIkCo",
        "media_label": "Watch the demo video",
    },
    {
        "name": "CampusEvac",
        "subtitle": "Student campus evacuation and emergency coordination",
        "recognition": "Recognised project",
        "team": "3 BUILDS",
        "project_type": "Campus safety",
        "source": "First Commit official project showcase",
        "media_type": "video",
        "media_url": "https://youtu.be/FhgTfCz0ou8",
        "media_label": "Watch the demo video",
    },
]


def calculate_aqi(day_num: int, pm25: float, pm10: float) -> float:
    """Calculate AQI using the model coefficients saved with the project."""
    if not isinstance(day_num, int) or isinstance(day_num, bool):
        raise ValueError("day_num must be an integer")
    if not all(math.isfinite(value) for value in (pm25, pm10)):
        raise ValueError("PM2.5 and PM10 must be finite numbers")
    if day_num < 0 or pm25 < 0 or pm10 < 0:
        raise ValueError("day_num, PM2.5, and PM10 must be non-negative")

    features = MODEL_PARAMS_DATA["features"]
    coefficients = MODEL_PARAMS_DATA["coef"]
    if features != ["day_num", "PM2.5", "PM10"] or len(coefficients) != 3:
        raise ValueError("Unsupported model feature configuration")

    predicted = (
        float(MODEL_PARAMS_DATA["intercept"])
        + float(coefficients[0]) * day_num
        + float(coefficients[1]) * pm25
        + float(coefficients[2]) * pm10
    )
    return round(max(0.0, predicted), 2)


def _aqi_category(aqi: float) -> str:
    """CPCB National AQI categories (India)."""
    for threshold, category in (
        (50, "Good"),
        (100, "Satisfactory"),
        (200, "Moderate"),
        (300, "Poor"),
        (400, "Very Poor"),
    ):
        if aqi <= threshold:
            return category
    return "Severe"


def _risk_level(aqi: float) -> str:
    if aqi <= 50:
        return "Minimal exposure risk"
    if aqi <= 100:
        return "Low exposure risk"
    if aqi <= 200:
        return "Moderate exposure risk"
    if aqi <= 300:
        return "High exposure risk"
    if aqi <= 400:
        return "Very high exposure risk"
    return "Severe exposure risk"


def _recommendation_for_aqi(aqi: float) -> str:
    if aqi <= 50:
        return "Air quality is good. Outdoor activity is fine for everyone."
    if aqi <= 100:
        return "Sensitive people may feel minor breathing discomfort. Most people can carry on as normal."
    if aqi <= 200:
        return "People with asthma, lung or heart disease may feel discomfort. Take it easy outdoors."
    if aqi <= 300:
        return "Most people may feel discomfort on prolonged exposure. Cut back on long outdoor activity."
    if aqi <= 400:
        return "Prolonged exposure may cause respiratory illness. Keep outdoor time short."
    return "Serious health effects are possible even for healthy people. Avoid outdoor exposure."


def _safety_actions(aqi: float) -> list[str]:
    if aqi <= 50:
        return ["Good for regular outdoor activity.", "Maintain normal routines and stay hydrated."]
    if aqi <= 100:
        return ["Sensitive people should watch for symptoms.", "Reduce very long outdoor exertion if you feel discomfort."]
    if aqi <= 200:
        return ["Reduce prolonged outdoor exertion if you have asthma or heart or lung disease.", "Keep reliever medication handy."]
    if aqi <= 300:
        return ["Wear a well-fitted N95/FFP2 mask outdoors.", "Move intense exercise indoors."]
    if aqi <= 400:
        return ["Limit outdoor travel to what is necessary.", "Use an air purifier in the rooms you spend time in."]
    return ["Avoid all non-essential outdoor exposure.", "Keep children and elders indoors and follow official advisories."]


def _safe_window(aqi: float) -> str:
    """General guidance only: not derived from hourly data."""
    if aqi <= 50:
        return "Any time of day"
    if aqi <= 100:
        return "Any time; sensitive people should avoid long exertion"
    if aqi <= 200:
        return "Short outdoor activity is fine; avoid long exertion"
    if aqi <= 300:
        return "Keep outdoor time brief"
    if aqi <= 400:
        return "Avoid outdoor exercise today"
    return "Stay indoors where possible"


def predict_aqi(day_num: int, pm25: float, pm10: float, audience: str = "general") -> dict[str, Any]:
    """Return a prediction, risk tier, and practical safety guidance."""
    predicted = calculate_aqi(day_num, pm25, pm10)
    category = _aqi_category(predicted)
    audience_key = str(audience or "general").strip().lower()
    audience_profile = {
        "general": "Reduce outdoor exertion and keep indoor air cleaner during this period.",
        "children": "Keep children indoors for longer periods and avoid school play in heavy pollution.",
        "elderly": "Limit outdoor exposure and avoid prolonged walks or commuting in poor air quality.",
        "outdoor": "Plan outdoor work around safer windows and take breaks indoors whenever possible.",
        "asthma": "Avoid strenuous activity and keep medication nearby; consider a mask on high-AQI hours.",
    }.get(audience_key, "Reduce outdoor exertion and keep indoor air cleaner during this period.")

    return {
        "predicted_aqi": predicted,
        "category": category,
        "risk_level": _risk_level(predicted),
        "recommendation": audience_profile,
        "safe_window": _safe_window(predicted),
        "safety_actions": _safety_actions(predicted),
        "features": {"day_num": day_num, "pm25": pm25, "pm10": pm10},
    }


class Response:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def get_json(self) -> dict[str, Any]:
        return self._payload


class Application:
    def test_client(self) -> "TestClient":
        return TestClient(self)

    def handle_request(self, method: str, path: str, body: str | None = None) -> Response:
        if method == "GET" and path == "/api/health":
            return Response(200, {"status": "ok", "service": "airroute"})
        if method == "GET" and path == "/api/projects":
            return Response(200, {"projects": PROJECTS, "source": "Official First Commit showcase"})
        if method == "POST" and path == "/api/predict":
            try:
                payload = json.loads(body or "{}")
                result = predict_aqi(
                    day_num=int(payload.get("day_num", 0)),
                    pm25=float(payload.get("pm25", 0)),
                    pm10=float(payload.get("pm10", 0)),
                    audience=str(payload.get("audience", "general")),
                )
                return Response(200, result)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                return Response(400, {"error": str(exc)})
        if method == "POST" and path == "/api/planner":
            try:
                payload = json.loads(body or "{}")
                title = str(payload.get("title", "")).strip()
                track = str(payload.get("track", "General")).strip()
                if not title:
                    raise ValueError("Task title is required")
                task = {
                    "id": len(PROJECTS) + 1,
                    "title": title,
                    "track": track,
                    "status": "Ready to plan",
                    "created_at": "Just now",
                }
                return Response(200, {"task": task, "message": "Project task added"})
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                return Response(400, {"error": str(exc)})
        return Response(404, {"error": "Not found"})


class TestClient:
    def __init__(self, application: Application) -> None:
        self.application = application

    def get(self, path: str) -> Response:
        return self.application.handle_request("GET", path)

    def post(self, path: str, data: str, content_type: str = "application/json") -> Response:
        del content_type
        return self.application.handle_request("POST", path, data)


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            response = app.handle_request("GET", self.path)
            self._send_json(response.get_json(), response.status_code)
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path not in ("/api/predict", "/api/planner"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8")
        response = app.handle_request("POST", self.path, payload)
        self._send_json(response.get_json(), response.status_code)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


app = Application()


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"AirRoute is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
