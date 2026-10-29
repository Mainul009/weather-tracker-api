# Weather Tracker API

A Flask-based REST API for managing weather locations, forecasts, observations, alerts, tracking, and analytics.

## Features

- User registration and authentication
- Location search, filtering, and nearby lookup
- Forecast and observation CRUD endpoints
- Weather analytics and rankings
- Alerts and tracking features
- MongoDB-backed storage

## Tech Stack

- Python 3
- Flask
- PyMongo
- Flask-CORS
- JWT authentication
- MongoDB

## Requirements

- Python 3.10+
- MongoDB running locally or configured via environment variables

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```env
   MONGO_URI=mongodb://127.0.0.1:27017
   DB_NAME=weatherDB
   SECRET_KEY=change-me
   PORT=5000
   FLASK_DEBUG=False
   ```

4. Run the app:
   ```bash
   python app.py
   ```

The API will start on `http://localhost:5000` by default.

## API Base URL

```text
/api/v1
```

## Example Endpoints

- `GET /api/v1/locations`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/analytics/hottest`

## Notes

- The project expects a running MongoDB instance.
- Some endpoints require admin access or valid JWT tokens.
