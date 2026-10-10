# AirRoute Frontend

The dashboard is a responsive, dependency-free interface for the AirRoute AQI predictor.

## Run

From the repository root:

```powershell
python backend\app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

The Python server serves the frontend and exposes:

- GET /api/health
- POST /api/predict
