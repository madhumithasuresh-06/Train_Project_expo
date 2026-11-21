# RailSense

RailSense is a full-stack, delay-aware railway assistant for Tamil Nadu. It predicts train delays, explains the contributing factors, and recommends faster direct or connecting alternatives when a booked journey may miss the user's deadline.

## Features

- Random Forest delay prediction for train and weekday combinations
- SHAP-based explanations for weather, season, weekday, and train type
- Manual delay override
- Deadline-based alternative route filtering
- Four-level recommendation engine:
  - Level 1: Direct express or superfast train
  - Level 2: Direct local, passenger, or suburban train
  - Level 3: Hub-based connecting journey
  - Level 4: TNSTC or SETC bus fallback
- Travel-class seat availability filtering
- Interactive station and route map
- Live RailKit status integration when an API key is configured

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 6, Tailwind CSS, Framer Motion, TanStack Query, React Leaflet |
| Backend | Node.js, Express.js |
| ML service | Python, FastAPI, Uvicorn, scikit-learn, SHAP, pandas, NumPy, joblib |
| Data | CSV datasets, in-memory graphs, Better SQLite support |

## Project Structure

```text
Railway_NIT/
├── frontend/       React and Vite web application
├── backend/        Express REST API and recommendation engine
├── ml_service/     FastAPI delay prediction service
├── data/           Railway, station, seat, route, and bus datasets
├── .venv/          Python virtual environment
└── scripts/        Data generation and maintenance utilities
```

## Prerequisites

- Node.js 18 or newer
- npm
- Python 3.10 or newer

## Installation

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install fastapi uvicorn scikit-learn pandas numpy shap joblib

cd frontend
npm install

cd ..\backend
npm install
```

## Configuration

Copy the example environment file and optionally add a RailKit API key:

```powershell
Copy-Item .env.example .env
```

The backend reads these settings:

```dotenv
RAILKIT_API_KEY=your_railkit_api_key_here
PORT=3001
```

The API key is optional. When it is not configured, live RailKit status will be reported as unavailable.

## Running the Application

Run each service in a separate PowerShell terminal.

### 1. ML service

```powershell
cd ml_service
..\.venv\Scripts\python.exe app.py
```

Runs at <http://localhost:8000>.

### 2. Backend

```powershell
cd backend
npm run dev
```

Runs at <http://localhost:3001>.

### 3. Frontend

```powershell
cd frontend
npm run dev
```

Open the local URL printed by Vite. It is normally <http://localhost:5173>; if that port is occupied, Vite may use <http://localhost:5174>.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Backend and graph health |
| GET | `/api/stations` | All railway stations |
| GET | `/api/trains` | All trains |
| GET | `/api/route-trains?source=CGL&destination=MDU` | Trains serving a selected route |
| GET | `/api/predict-delay?train_number=12635&day=Sat` | Predicted delay and explanations |
| POST | `/api/recommend` | Delay-aware route recommendations |
| GET | `/api/live-delay?train_number=12635&day=Sat` | Combined prediction and live status |

Example recommendation request:

```json
{
  "source_station": "CGL",
  "destination_station": "MDU",
  "train_number": "12635",
  "day": "Sat",
  "threshold_minutes": 15,
  "travel_class": "SL",
  "manual_delay_minutes": 60
}
```

## ML Model

The ML microservice loads pre-trained joblib artifacts from `ml_service/models/`:

- Random Forest delay model
- Day, train type, season, and weather encoders
- Train type mapping

The prediction input includes weekday, train type, season, and weather. SHAP values identify the strongest positive or negative delay contributors.

To retrain the model:

```powershell
cd ml_service
..\.venv\Scripts\python.exe train_model.py
```

## Recommendation Flow

1. Validate the source station, destination station, and booked train.
2. Predict the delay or apply a manual delay override.
3. Compare the effective delay with the selected threshold.
4. If the threshold is exceeded, calculate the delayed ETA.
5. Search direct express, local, connecting, and bus alternatives.
6. Return alternatives that meet the deadline and available-seat requirements.

## Troubleshooting

- **Frontend opens on the wrong port:** Open the exact URL printed by Vite.
- **Backend cannot start:** Run `npm install` inside `backend/` and verify the data files exist.
- **ML service cannot find models:** Run from `ml_service/` and confirm `ml_service/models/*.joblib` exists.
- **Live delay is unavailable:** Add a valid `RAILKIT_API_KEY` to `.env`.
- **No alternatives are returned:** Try another valid route or increase the manual delay and threshold.

## Future Enhancements

- Live IRCTC and bus-network feeds
- Live weather and congestion data
- Stored journeys and delay alerts
- Booking deep links
- Automated backend and end-to-end tests
