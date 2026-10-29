# Weather Tracker API

[![CI](https://github.com/Mainul009/weather-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Mainul009/weather-tracker-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)

A production-minded Flask API for tracking weather locations, forecasts, observations, alerts, and analytics.

## Why this project

This project provides a clean backend for weather data workflows, including:

- location discovery and filtering
- forecast and observation management
- alert and tracking features
- analytics such as rankings and condition summaries
- MongoDB-backed persistence with index creation

## Architecture

The application is organized around a modular Flask blueprint structure:

- `app.py` — app factory and entrypoint
- `blueprints/` — route modules for auth, locations, forecasts, observations, analytics, tracker, and alerts
- `db.py` — MongoDB collections and index setup
- `config.py` — configuration and environment loading
- `utils.py` and `validators.py` — shared helpers and request validation
- `decorators.py` — auth and authorization guards

## Tech stack

- Python 3.11+
- Flask 3.x
- PyMongo
- MongoDB
- JWT authentication
- Flask-CORS
- pytest for automated smoke testing

## Quick start

### 1) Create a virtual environment

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

For development and testing:

```bash
pip install -r requirements-dev.txt
```

### 3) Configure environment variables

Copy the example file and update values if needed:

```bash
copy .env.example .env
```

Then set your values:

```env
MONGO_URI=mongodb://127.0.0.1:27017
DB_NAME=weatherDB
SECRET_KEY=change-me-to-a-long-random-secret
PORT=5000
FLASK_DEBUG=False
```

### 4) Run the service

```bash
python app.py
```

The app starts on:

```text
http://localhost:5000
```

## API overview

All routes are prefixed with:

```text
/api/v1
```

Common examples:

- `GET /api/v1/locations`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/analytics/hottest`
- `GET /api/v1/analytics/rainiest`
- `GET /api/v1/analytics/windiest`

## Project status

This repository is structured for ongoing development and includes:

- CI validation with GitHub Actions
- dependency separation for app vs dev tooling
- a basic smoke test for app startup and blueprint registration
- environment variable templating

## Roadmap

Planned improvements include:

- richer API documentation with OpenAPI/Swagger
- more robust test coverage for endpoints and auth flows
- request rate limiting and monitoring
- background job support for weather ingestion
- Docker support for easier deployment

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes with clear messages
4. Open a pull request with a summary of your work

## License

This project is licensed under the [MIT License](LICENSE).
