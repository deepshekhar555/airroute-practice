import json
import unittest
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import app, predict_aqi


class PredictionTests(unittest.TestCase):
    def test_predict_aqi_uses_existing_model_parameters(self):
        result = predict_aqi(day_num=2000, pm25=150, pm10=250)
        self.assertEqual(result["predicted_aqi"], 256.12)
        self.assertEqual(result["category"], "Poor")

    def test_predict_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            predict_aqi(day_num=-1, pm25=150, pm10=250)
        with self.assertRaises(ValueError):
            predict_aqi(day_num=1, pm25=-1, pm10=250)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")

    def test_prediction_endpoint(self):
        response = self.client.post(
            "/api/predict",
            data=json.dumps({"day_num": 2000, "pm25": 150, "pm10": 250}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["predicted_aqi"], 256.12)
        self.assertIn("risk_level", data)
        self.assertIn("recommendation", data)
        self.assertIn("safe_window", data)
        self.assertTrue(data["safety_actions"])

    def test_prediction_endpoint_rejects_invalid_json(self):
        response = self.client.post(
            "/api/predict",
            data=json.dumps({"day_num": -1, "pm25": 150, "pm10": 250}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_project_showcase_is_available(self):
        response = self.client.get("/api/projects")
        self.assertEqual(response.status_code, 200)
        projects = response.get_json()["projects"]
        self.assertTrue(any(project["name"] == "Suraksha" for project in projects))
        self.assertTrue(any(project["name"] == "Beacon Night Shift" for project in projects))
        self.assertTrue(all("media_type" in project for project in projects))
        self.assertTrue(any(project["media_type"] == "video" for project in projects))

    def test_project_planner_accepts_a_task(self):
        response = self.client.post(
            "/api/planner",
            data=json.dumps({"title": "Build AQI dashboard", "track": "Air"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["task"]["title"], "Build AQI dashboard")
        self.assertEqual(data["task"]["track"], "Air")


if __name__ == "__main__":
    unittest.main()
