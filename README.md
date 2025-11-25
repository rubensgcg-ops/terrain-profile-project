
# Terrain Profile Tool (Flask)

An interactive tool for analyzing **elevation profiles** between two points selected on a map. The application combines **Flask (backend)**, **Leaflet (map)**, and **Plotly (charting)** to generate detailed terrain information along a route.

## Features

- **Interactive map selection**: Click two points directly on the map to define start and end points
- **Automatic calculations**:
  - Total route distance (meters and kilometers)
  - Total sampling points (based on points per km setting)
  - Maximum elevation along the route
  - Relative elevation gain from start point
- **Interactive elevation profile**: Visualized with Plotly
- **Map highlighting**: Click any point on the graph to highlight it on the map
- **CSV export**: Download complete profile data with all coordinates and elevations
- **Block-based requests**: Handles long-distance routes (up to 100+ km) without API failures
- **Automatic fallback**: Falls back to alternative service if primary API fails

## Elevation Data Sources

The application uses elevation data from **Digital Elevation Models (DEM)**.

### 1. OpenTopoData – SRTM 30m (Primary)

**API**: <https://api.opentopodata.org>

- Based on NASA's SRTM v3.0 model
- ~30 meter resolution
- 10-16 meter average accuracy
- Supports ~100 coordinates per request
- Primary data source for the application

### 2. Open-Elevation (Fallback)

**API**: <https://open-elevation.com/>

- Used only when the primary API fails
- Also based on SRTM data
- Returns one coordinate per request
- Variable precision

## Why Use Block-Based Requests?

Public elevation APIs limit the number of coordinates per request. OpenTopoData, for example, starts returning `null` when requests contain more than ~100 points.

To ensure stability:

- Routes are automatically divided into blocks of up to **100 points**
- Each block is queried separately
- Responses are combined on the backend
- If a block fails, it's retried via the Open-Elevation fallback

This allows calculating profiles for **20 km, 40 km, or even 100+ km routes** safely.

## Project Structure

```
terrain-profile-project/
├── server.py              # Flask backend with elevation API endpoints
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── frontend/
    ├── index.html        # Web interface with map and chart
    └── style.css         # Styling
```

## Installation & Setup

### 1. (Optional) Create a Virtual Environment

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Server

```bash
python server.py
```

The application will be available at:

- **Local machine**: <http://localhost:8000>
- **Network access**: <http://YOUR_IP:8000>

## How to Use

1. Open the interface in your browser
2. Click on the map once to set the **start point**
3. Click another location to set the **end point**
4. The interface will automatically display:
   - Total distance
   - Total number of sampling points
   - Elevation profile chart
   - Maximum elevation and relative elevation gain
5. Click any point on the chart to highlight it on the map
6. Click **Export CSV** to download the detailed data

## Resolution Adjustment

You can configure how many sampling points you want per kilometer:

```text
n = distance_km × points_per_km
```

**Recommendations:**

- **20–50 points/km**: Long profiles (> 30 km)
- **50–150 points/km**: General use
- **150–300 points/km**: High precision, short routes

## Accuracy Considerations

SRTM data is suitable for general estimates, but:

- Does not represent buildings, towers, or artificial obstacles
- May be smoothed in urban areas
- Can have errors of tens of meters in mountainous regions
- Does not replace professional surveying

## Requirements

The `requirements.txt` file contains:

```txt
flask
flask-cors
requests
numpy
```

All dependencies are automatically installed via `pip install -r requirements.txt`.

