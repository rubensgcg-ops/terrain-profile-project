from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import numpy as np
import requests
import io
import csv
import math
import os

# =======================================
# CONFIGURAÇÃO DO FLASK
# =======================================

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# =======================================
# FRONTEND (SERVE index.html + arquivos estáticos)
# =======================================

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("frontend", path)

# =======================================
# FUNÇÕES AUXILIARES
# =======================================

def interpolate(start, end, n=200):
    lat1, lon1 = start
    lat2, lon2 = end
    lats = np.linspace(lat1, lat2, n)
    lons = np.linspace(lon1, lon2, n)
    return list(zip(lats.tolist(), lons.tolist()))

def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))
    return R * c

# =======================================
# ENDPOINT: /profile
# (agora com REQUISIÇÕES EM BLOCOS!)
# =======================================

@app.route("/profile")
def profile():
    try:
        lat1 = float(request.args.get("lat1"))
        lon1 = float(request.args.get("lon1"))
        lat2 = float(request.args.get("lat2"))
        lon2 = float(request.args.get("lon2"))
        n    = int(request.args.get("n", 200))
    except:
        return jsonify({"error": "Parâmetros inválidos"}), 400

    points = interpolate((lat1, lon1), (lat2, lon2), n)

    # ============================
    # CHAMADA EM BLOCOS (NOVO!)
    # ============================

    def fetch_block(block):
        coords_str = "|".join([f"{p[0]},{p[1]}" for p in block])
        url = "https://api.opentopodata.org/v1/srtm30m"
        r = requests.get(url, params={"locations": coords_str}, timeout=25)
        return r.json().get("results", [])

    BLOCK_SIZE = 100
    elevations = []

    for i in range(0, len(points), BLOCK_SIZE):
        block_points = points[i:i+BLOCK_SIZE]

        try:
            results = fetch_block(block_points)
            block_elev = [r.get("elevation", None) for r in results]

        except:
            # fallback para Open-Elevation ponto a ponto
            block_elev = []
            for lat, lon in block_points:
                try:
                    r = requests.get(
                        "https://api.open-elevation.com/api/v1/lookup",
                        params={"locations": f"{lat},{lon}"},
                        timeout=10
                    )
                    block_elev.append(
                        r.json()["results"][0]["elevation"]
                    )
                except:
                    block_elev.append(None)

        elevations.extend(block_elev)

    # ============================
    # DISTÂNCIA CUMULATIVA
    # ============================

    distances = [0.0]
    for i in range(1, len(points)):
        distances.append(distances[-1] + haversine(points[i-1], points[i]))

    # ============================
    # MAIOR ELEVAÇÃO
    # ============================

    valid = [(i, e) for i, e in enumerate(elevations) if e is not None]
    if valid:
        max_idx, max_elev = max(valid, key=lambda x: x[1])
    else:
        max_idx, max_elev = None, None

    return jsonify({
        "points": points,
        "elevations": elevations,
        "distances": distances,
        "max_index": max_idx,
        "max_elevation": max_elev
    })

# =======================================
# ENDPOINT: /profile_csv
# =======================================

@app.route("/profile_csv")
def profile_csv():
    try:
        lat1 = float(request.args.get("lat1"))
        lon1 = float(request.args.get("lon1"))
        lat2 = float(request.args.get("lat2"))
        lon2 = float(request.args.get("lon2"))
        n    = int(request.args.get("n", 200))
    except:
        return jsonify({"error": "Parâmetros inválidos"}), 400

    # Chamamos o próprio endpoint profile
    data = profile().json if hasattr(profile(), "json") else profile()

    points     = data["points"]
    elevations = data["elevations"]
    distances  = data["distances"]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["index", "lat", "lon", "elevation", "distance_m"])

    for i, p in enumerate(points):
        writer.writerow([i, p[0], p[1], elevations[i], distances[i]])

    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=profile.csv"}
    )

# =======================================
# RUN SERVER
# =======================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
