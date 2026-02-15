import { create } from 'zustand'

export interface BoundaryCondition {
  id: string
  type: 'fixation' | 'force' | 'pressure' | 'temperature'
  name: string
  selectionType: 'faces' | 'vertices'
  selectionIds: number[]
  forceVector?: number[]
  pressureValue?: number
  temperatureValue?: number
  fixedDofs?: string[]
}

interface Geometry {
  id: string
  filename: string
  format: string
  vertices_count: number
  faces_count: number
  bounding_box?: { min: number[]; max: number[] }
  volume?: number
}

interface MeshData {
  vertices: number[][]
  faces: number[][]
  normals?: number[][]
}

interface OptimizationResult {
  job_id: string
  status: string
  result?: {
    result_id: string
    final_compliance: number
    iterations: number
  }
}

interface Store {
  // Geometry
  geometry: Geometry | null
  setGeometry: (geometry: Geometry | null) => void

  // Mesh data for 3D viewer
  meshData: MeshData | null
  setMeshData: (data: MeshData | null) => void

  // Boundary conditions
  boundaryConditions: BoundaryCondition[]
  addBoundaryCondition: (bc: BoundaryCondition) => void
  removeBoundaryCondition: (id: string) => void
  updateBoundaryCondition: (id: string, updates: Partial<BoundaryCondition>) => void

  // Optimization
  optimizationResult: OptimizationResult | null
  setOptimizationResult: (result: OptimizationResult | null) => void

  // UI
  showWireframe: boolean
  toggleWireframe: () => void
}

export const useStore = create<Store>((set) => ({
  // Geometry
  geometry: null,
  setGeometry: (geometry) => set({ geometry }),

  // Mesh
  meshData: null,
  setMeshData: (meshData) => set({ meshData }),

  // Boundary conditions
  boundaryConditions: [],
  addBoundaryCondition: (bc) =>
    set((state) => ({
      boundaryConditions: [...state.boundaryConditions, bc],
    })),
  removeBoundaryCondition: (id) =>
    set((state) => ({
      boundaryConditions: state.boundaryConditions.filter((bc) => bc.id !== id),
    })),
  updateBoundaryCondition: (id, updates) =>
    set((state) => ({
      boundaryConditions: state.boundaryConditions.map((bc) =>
        bc.id === id ? { ...bc, ...updates } : bc
      ),
    })),

  // Optimization
  optimizationResult: null,
  setOptimizationResult: (optimizationResult) => set({ optimizationResult }),

  // UI
  showWireframe: false,
  toggleWireframe: () => set((state) => ({ showWireframe: !state.showWireframe })),
}))
