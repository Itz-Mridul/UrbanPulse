# UrbanPulse - Pune Urban Intelligence Dashboard

UrbanPulse is a real-time, 3D interactive dashboard designed to monitor cascading hazards (like extreme rainfall, floods, and landslides) in the Pune Metro Region.

## Features
- **Interactive 3D Map**: Built with Mapbox GL JS v3, featuring real-world building extrusions, terrain, and dusk lighting.
- **Hazard Simulation**: Visualizes the cascading effects of extreme rainfall using real-time data overlays and animations.
- **Backend Integration**: FastAPI backend built to calculate hazard probabilities and stream live alerts via WebSockets.
- **Frontend Framework**: The primary dashboard is built natively in HTML/CSS/JS (`index.html`) for maximum performance, with a secondary React application (`frontend/`).

## Quick Start (Dashboard)
To view the 3D dashboard:
1. Simply open `index.html` in your browser.
2. If it does not load properly due to CORS restrictions, serve the directory locally:
   ```bash
   python3 -m http.server 8080
   ```
   Then navigate to `http://localhost:8080/index.html`.

## Backend API
The backend is built with FastAPI and handles live hazard predictions and alert streaming. Copy `.env.example` to the project root for Docker Compose, or to `backend/.env` when running the backend directly. Fill in every blank value before starting:
```bash
cp .env.example backend/.env
# Generate a secret key with: openssl rand -hex 32
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Set `DATABASE_URL` and `DATABASE_URL_SYNC` to connection URLs that use the same password as `POSTGRES_PASSWORD`. Use `localhost` as the database host when running the backend directly, or `db` when using Docker Compose. Do not commit your `.env` file.

The Mapbox map requires an access token. Set `VITE_MAPBOX_TOKEN` in `frontend/.env` for the React dashboard. For the standalone `index.html`, copy `mapbox-config.example.js` to `mapbox-config.js` and set `window.URBANPULSE_MAPBOX_TOKEN` there. Keep tokens private and restrict them to the domains where the dashboard is hosted.

## Technologies Used
- **Mapbox GL JS v3** (Standard Style)
- **HTML5 / CSS3 / Vanilla JS**
- **Chart.js**
- **Python / FastAPI** (Backend)
- **React / Vite** (Alternative Frontend)
