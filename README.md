# AirRoute Delhi — AQI Safety & Action Dashboard

AirRoute is an environmental health project for the AWS Environmental Hacks track. It focuses on the real-world problem of air pollution risk in Delhi, helping people understand when exposure is unsafe and which actions are safest for different user groups.

## Features

- Predict AQI from day number, PM2.5, and PM10 inputs.
- Show AQI category, risk level, and a safe outdoor window.
- Provide personalized guidance for children, elders, outdoor workers, and asthma-sensitive users.
- Translate model predictions into practical health and safety actions.
- Serve the dashboard and API from one local command.
- Reuse the saved model coefficients in `backend/package/model_params.json`.
- Run without external JavaScript or Python packages.

## Structure

- `backend/`: API, model training, prediction, and tests.
- `data/`: Delhi AQI and city/station datasets.
- `frontend/`: responsive dashboard and client-side interaction.
- `models/`: trained model artifact (`aqi_model.pkl`).

## Run locally

From the repository root:

```powershell
python backend\app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

The API endpoints are:

- `GET /api/health`
- `POST /api/predict` with JSON such as `{"day_num":2000,"pm25":150,"pm10":250,"audience":"children"}`

The response includes the predicted AQI, risk level, recommended safe window, and actionable steps for the selected audience.

## Tests

```powershell
python -m unittest discover -s backend/tests -v
```

## AWS Lambda

The original Lambda handler remains available in `backend/lambda_function.py`. The project is designed to work locally first, while remaining suitable for deployment to AWS Lambda or a static frontend plus API architecture.
