# TopoOpt Web 🏗️

Progressive Web App für Topologie-Optimierung in 3D.

## Features

- 🎯 3D-Viewer mit Import/Export (STL, STEP, OBJ, glTF)
- 📐 Randbedingungen definieren (Fixierungen, Kräfte, Drucklasten, Temperatur)
- ⚡ SIMP-Optimierer (Solid Isotropic Material with Penalization)
- 🐳 Docker One-Click Deployment

## Tech Stack

| Komponente | Technologie |
|-----------|------------|
| Frontend | React + Three.js + Tailwind CSS |
| Backend | Python + FastAPI |
| Solver | SIMP (scipy), FEniCS |
| 3D-Formate | OpenCascade (STEP), numpy-stl (STL), trimesh (OBJ/glTF) |
| Deployment | Docker Compose |

## Schnellstart

```bash
# Mit Docker
docker-compose up --build

# Frontend öffnen
open http://localhost:3000

# API Docs
open http://localhost:8000/docs
```

## Entwicklung

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # oder venv\\Scripts\\activate (Windows)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Projektstruktur

```
topo-opt-web/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI App
│   │   ├── api/             # API Routes
│   │   ├── core/            # Config, Settings
│   │   ├── models/          # Pydantic Models
│   │   ├── services/        # Business Logic
│   │   └── solver/          # SIMP Optimizer
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React Components
│   │   ├── hooks/           # Custom Hooks
│   │   ├── store/           # State Management
│   │   └── utils/           # Utilities
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Roadmap

- [x] Phase 1: MVP (3D Viewer, Import, BCs, SIMP Solver, Export)
- [x] Phase 2: CAD-Style BCs, Named Selections, STEP Export
- [x] Phase 3: PWA Offline, Job Queue, fly.io Deploy

**Stand 2026:** Backend enthält eine asynchrone Optimierungs-Warteschlange mit Status-API, Frontend ist als installierbare PWA mit Service Worker konfiguriert.


### Browser-Standalone (ohne Server/Python/Docker)

- Öffne `frontend/public/topo-opt-standalone.html` direkt im Browser (Doppelklick / `file://`).
- Die Datei ist vollständig eigenständig lauffähig: keine lokale Python-API, kein lokaler Webserver, kein Docker nötig.
- Lokale Berechnung läuft in **WebWorkern** mit einstellbarer Workerzahl und optionalem GPU-Pfad (WebGPU-Erkennung).
- Optional kann auf externe Server/Cloud ausgelagert werden: API-Base-URL im UI setzen und Remote-Run starten.
- Ergebnisexport erfolgt als JSON direkt im Browser.


### fly.io Deploy (Phase 3)

Backend ist für fly.io vorbereitet.

```bash
# Fly CLI installieren und einloggen
fly auth login

# App erstellen (einmalig)
fly launch --no-deploy

# Volume für Uploads/Results
fly volumes create topo_opt_data --region fra --size 10

# Deploy
fly deploy
```

Healthcheck: `GET /health`

## Lizenz

MIT
