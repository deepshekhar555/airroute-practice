# AirRoute (practice)

Air quality (AQI) prediction for Indian cities, with a trained model and an AWS Lambda backend.

## Structure
- `backend/`: data exploration, model training/export, local prediction, and the Lambda function
- `data/`: cleaned Delhi AQI data and daily city/station CSVs
- `models/`: trained model (`aqi_model.pkl`)

## Dataset
The large hourly files are not stored in this repo. Download the
"Air Quality Data in India" dataset from Kaggle and place
`city_hour.csv` and `station_hour.csv` in the `data/` folder.

## Run locally
