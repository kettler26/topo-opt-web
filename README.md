# TopoOpt Web 🏗️

A full-stack progressive web application for structural topology optimization. Combine an intuitive React-based 3D interface with a powerful Python backend to perform SIMP (Solid Isotropic Material with Penalization) optimization. Import geometries in multiple formats (STL, STEP, OBJ, glTF), define boundary conditions intuitively, run optimization simulations, and export optimized results. Perfect for engineers and designers seeking to reduce material usage while maintaining structural integrity.

## Features

- 🎯 **3D Viewer** – Interactive 3D model visualization with real-time rendering
- 📥 **Multi-Format Import** – Load STL, STEP, OBJ, and glTF files
- 📤 **Multi-Format Export** – Save optimized designs in STL, STEP, OBJ, and glTF
- 📐 **Boundary Conditions** – Define fixations, point loads, pressure loads, and thermal conditions
- ⚡ **SIMP Solver** – State-of-the-art Solid Isotropic Material with Penalization optimization
- 🎨 **Intuitive UI** – CAD-style interface with Tailwind CSS styling
- 🐳 **One-Click Deployment** – Docker Compose for instant setup
- 📱 **Progressive Web App** – Responsive design for desktop and tablet use

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | React 18 + TypeScript + Three.js + Tailwind CSS |
| **Backend** | Python 3.11+ + FastAPI |
| **Solver** | SIMP algorithm (scipy), FEniCS for FEM computation |
| **3D Formats** | OpenCascade (STEP), numpy-stl (STL), trimesh (OBJ/glTF) |
| **Deployment** | Docker & Docker Compose |
| **License** | MIT |

## Quick Start

### With Docker (Recommended)

```bash
# Clone and navigate to the repository
git clone https://github.com/kettler26/topo-opt-web.git
cd topo-opt-web

# Build and start services
docker-compose up --build

# Open in browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

## Project Structure

```
topo-opt-web/
├── backend/                    # Python FastAPI application
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── api/               # REST API endpoints
│   │   ├── core/              # Configuration & settings
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # Business logic & workflows
│   │   └── solver/            # SIMP topology optimization engine
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile
│
├── frontend/                   # React + TypeScript application
│   ├── src/
│   │   ├── components/        # React UI components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── store/             # State management
│   │   ├── utils/             # Helper utilities
│   │   └── App.tsx            # Main application
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
└── docker-compose.yml         # Multi-container orchestration
```

## Usage Workflow

1. **Import Geometry** – Load your CAD model (STL, STEP, OBJ, or glTF)
2. **Define Boundary Conditions** – Set fixed regions, apply loads and constraints
3. **Configure Optimization** – Adjust material removal ratio, iterations, and parameters
4. **Run Optimization** – Execute SIMP solver to generate optimized topology
5. **Visualize Results** – View stress distribution and optimized geometry in real-time
6. **Export Design** – Save the optimized model in your preferred format

## API Documentation

Once running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Roadmap

- [x] **Phase 1** – MVP: 3D Viewer, Import/Export, Boundary Conditions, SIMP Solver
- [ ] **Phase 2** – Advanced: CAD-Style BCs, Named Selections, STEP Export Optimization
- [ ] **Phase 3** – Production: PWA Offline Mode, Job Queue, Cloud Deployment (fly.io)

## Performance Considerations

- Optimization time varies based on mesh density and iteration count
- Recommend starting with coarser meshes for testing
- Larger models may require increased computational resources
- Browser 3D rendering optimized for modern WebGL implementations

## Troubleshooting

**Docker won't build?**
```bash
docker-compose down
docker system prune
docker-compose up --build
```

**Port conflicts?**
Edit `docker-compose.yml` to change ports (e.g., 3001 for frontend, 8001 for backend)

**Solver errors?**
Check Python dependencies and ensure FEniCS is properly installed in the Docker image

## Contributing

Contributions are welcome! Please feel free to:
- Report issues and suggest features
- Submit pull requests with improvements
- Improve documentation

## License

This project is licensed under the [MIT License](LICENSE) – feel free to use it in personal and commercial projects.

## Author

Developed by [kettler26](https://github.com/kettler26)

---

**Questions or feedback?** Feel free to open an issue or start a discussion!
