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
  // STEP-specific
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
  visible: boolean
  namedSelectionId?: string
  config: Record<string, unknown>
}

export interface ContactConditionData {
  id: string
  name: string
  contactType: string
  masterSelectionId: string
  slaveSelectionId: string
  frictionCoefficient: number
  active: boolean
}

export interface OptimizationConfig {
  volumeFraction: number
  penalty: number
  filterRadius: number
  maxIterations: number
  tolerance: number
}

export interface OptimizationJob {
  jobId: string
  status: string
  iteration: number
  maxIterations: number
  compliance: number
  change: number
  resultFileId?: string
}

interface AppStore {
  // Model
  model: ModelData | null
  setModel: (model: ModelData | null) => void

  // Boundary conditions
  boundaryConditions: BoundaryCondition[]
  addBoundaryCondition: (bc: BoundaryCondition) => void
  removeBoundaryCondition: (id: string) => void
  updateBoundaryCondition: (id: string, update: Partial<BoundaryCondition>) => void

  // Contact conditions
  contactConditions: ContactConditionData[]
  addContactCondition: (cc: ContactConditionData) => void
  removeContactCondition: (id: string) => void
  updateContactCondition: (id: string, update: Partial<ContactConditionData>) => void

  // Optimization
  optimizationConfig: OptimizationConfig
  setOptimizationConfig: (config: Partial<OptimizationConfig>) => void
  isOptimizing: boolean
  setIsOptimizing: (val: boolean) => void
  currentJob: OptimizationJob | null
  setCurrentJob: (job: OptimizationJob | null) => void

  // UI State
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

  boundaryConditions: [],
  addBoundaryCondition: (bc) => set((s) => ({ boundaryConditions: [...s.boundaryConditions, bc] })),
  removeBoundaryCondition: (id) => set((s) => ({ boundaryConditions: s.boundaryConditions.filter((b) => b.id !== id) })),
  updateBoundaryCondition: (id, update) => set((s) => ({
    boundaryConditions: s.boundaryConditions.map((b) => b.id === id ? { ...b, ...update } : b),
  })),

  contactConditions: [],
  addContactCondition: (cc) => set((s) => ({ contactConditions: [...s.contactConditions, cc] })),
  removeContactCondition: (id) => set((s) => ({ contactConditions: s.contactConditions.filter((c) => c.id !== id) })),
  updateContactCondition: (id, update) => set((s) => ({
    contactConditions: s.contactConditions.map((c) => c.id === id ? { ...c, ...update } : c),
  })),

  optimizationConfig: {
    volumeFraction: 0.4,
    penalty: 3.0,
    filterRadius: 1.5,
    maxIterations: 100,
    tolerance: 1e-4,
  },
  setOptimizationConfig: (config) => set((s) => ({
    optimizationConfig: { ...s.optimizationConfig, ...config },
  })),
  isOptimizing: false,
  setIsOptimizing: (val) => set({ isOptimizing: val }),
  currentJob: null,
  setCurrentJob: (job) => set({ currentJob: job }),

  viewMode: 'solid',
  setViewMode: (mode) => set({ viewMode: mode }),
  showGrid: true,
  setShowGrid: (v) => set({ showGrid: v }),
  showAxes: true,
  setShowAxes: (v) => set({ showAxes: v }),
}))
