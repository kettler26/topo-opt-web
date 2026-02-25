import { create } from 'zustand'

export interface MeshInfo {
  vertices?: number
  num_vertices?: number
  faces?: number
  num_faces?: number
  is_watertight?: boolean
  volume?: number | null
  surface_area?: number
  bounds_min?: number[]
  bounds_max?: number[]
  center?: number[]
  solids?: number
  edges?: number
  error?: string
}

export interface ModelData {
  fileId: string
  filename: string
  format: string
  meshInfo: MeshInfo | null
  geometryUrl: string | null
  namedSelections: NamedSelectionData[]
}

export interface NamedSelectionData {
  id: string
  name: string
  entityType: string
  entityIndices: number[]
  color: string
  visible: boolean
}

export interface BoundaryCondition {
  id: string
  type: string
  name: string
  visible?: boolean
  namedSelectionId?: string
  config?: Record<string, unknown>
  selectionType?: string
  selectionIds?: number[]
  forceVector?: number[]
  pressureValue?: number
  temperatureValue?: number
  fixedDofs?: string[]
}

export interface OptimizationResult {
  job_id: string
  status: string
  result?: {
    final_compliance?: number
    iterations?: number
  }
}

interface AppStore {
  model: ModelData | null
  setModel: (model: ModelData | null) => void
  meshData: { vertices: number[][]; faces: number[][]; normals?: number[][] } | null
  setMeshData: (meshData: { vertices: number[][]; faces: number[][]; normals?: number[][] } | null) => void

  boundaryConditions: BoundaryCondition[]
  addBoundaryCondition: (bc: BoundaryCondition) => void
  removeBoundaryCondition: (id: string) => void
  updateBoundaryCondition: (id: string, update: Partial<BoundaryCondition>) => void

  isOptimizing: boolean
  setIsOptimizing: (val: boolean) => void
  optimizationResult: OptimizationResult | null
  setOptimizationResult: (result: OptimizationResult | null) => void

  viewMode: 'solid' | 'wireframe' | 'solid+wireframe'
  setViewMode: (mode: 'solid' | 'wireframe' | 'solid+wireframe') => void
  showGrid: boolean
  setShowGrid: (v: boolean) => void
  showAxes: boolean
  setShowAxes: (v: boolean) => void
}

export const useModelStore = create<AppStore>((set) => ({
  model: null,
  setModel: (model) => set({ model }),
  meshData: null,
  setMeshData: (meshData) => set({ meshData }),

  boundaryConditions: [],
  addBoundaryCondition: (bc) => set((s) => ({ boundaryConditions: [...s.boundaryConditions, bc] })),
  removeBoundaryCondition: (id) => set((s) => ({ boundaryConditions: s.boundaryConditions.filter((b) => b.id !== id) })),
  updateBoundaryCondition: (id, update) => set((s) => ({
    boundaryConditions: s.boundaryConditions.map((b) => b.id === id ? { ...b, ...update } : b),
  })),

  isOptimizing: false,
  setIsOptimizing: (val) => set({ isOptimizing: val }),
  optimizationResult: null,
  setOptimizationResult: (optimizationResult) => set({ optimizationResult }),

  viewMode: 'solid',
  setViewMode: (mode) => set({ viewMode: mode }),
  showGrid: true,
  setShowGrid: (v) => set({ showGrid: v }),
  showAxes: true,
  setShowAxes: (v) => set({ showAxes: v }),
}))

export const useStore = useModelStore
