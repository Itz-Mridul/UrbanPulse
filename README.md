# UrbanPulse - Pune Urban Intelligence Dashboard

UrbanPulse is a real-time, 3D interactive dashboard designed to monitor cascading hazards (like extreme rainfall, floods, and landslides) in the Pune Metro Region. 

## Features
- **Interactive 3D Map**: Built with Mapbox GL JS v3, featuring real-world high-resolution satellite imagery, 3D building extrusions, and accurate topography.
- **Hazard Simulation**: Visualizes the cascading effects of extreme rainfall using real-time data overlays and animations.
- **Backend Integration**: FastAPI backend built to calculate hazard probabilities and stream live alerts via WebSockets.
- **Frontend Framework**: The primary dashboard is built natively in HTML/CSS/JS (`index.html`) for maximum performance, with a secondary React application (`frontend/`).

## System Architecture

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#1E293B,stroke:#00F0FF,stroke-width:2px,color:#fff;
    classDef backend fill:#0F172A,stroke:#FF3366,stroke-width:2px,color:#fff;
    classDef db fill:#020617,stroke:#FFCC33,stroke-width:2px,color:#fff;
    classDef external fill:#334155,stroke:#fff,stroke-width:1px,color:#fff;

    subgraph Frontend["Frontend Dashboard"]
        UI["User Interface<br>(HTML/JS/CSS & React)"]:::frontend
        Map["3D Interactive Map<br>(Mapbox GL JS)"]:::frontend
        UI <--> Map
    end

    subgraph Backend["FastAPI Backend Server"]
        API["REST API & WebSockets<br>(FastAPI)"]:::backend
        Pred["Hazard Prediction Models<br>(Python)"]:::backend
        API <--> Pred
    end

    subgraph Database["Data Layer"]
        DB[("PostgreSQL DB<br>w/ GeoAlchemy2")]:::db
    end

    subgraph External["External Data Feeds"]
        Weather["Real-time Weather APIs"]:::external
        Satellite["Satellite & DEM Data"]:::external
    end

    %% Connections
    Weather --> API
    Satellite --> Map
    Pred <--> DB
    API -- "Live Alerts (WebSocket)" --> UI
    API -- "Prediction Data (JSON)" --> Map
```

## Quick Start (Dashboard)
To view the 3D dashboard:
1. Simply open `index.html` in your browser. 
2. If it does not load properly due to CORS restrictions, serve the directory locally:
   ```bash
   python3 -m http.server 8080
   ```
   Then navigate to `http://localhost:8080/index.html`.

## Backend API
The backend is built with FastAPI and handles live hazard predictions and alert streaming.
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Technologies Used
- **Mapbox GL JS v3** (Satellite-Streets + 3D Terrain)
- **HTML5 / CSS3 / Vanilla JS**
- **Chart.js**
- **Python / FastAPI** (Backend)
- **React / Vite** (Alternative Frontend)
- **PostgreSQL & GeoAlchemy2** (Database)
