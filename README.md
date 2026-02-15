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
- [ ] Phase 2: CAD-Style BCs, Named Selections, STEP Export
- [ ] Phase 3: PWA Offline, Job Queue, fly.io Deploy

## Lizenz

MIT
