import { useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { api } from '../utils/api'
import { useStore } from '../store/useStore'
import type { BoundaryCondition } from '../store/useStore'
import { runLocalOptimization } from '../utils/localOptimizer'

type ExecutionMode = 'local' | 'server' | 'cloud'
type ComputeDevice = 'cpu' | 'gpu'

const CLOUD_API_URL = import.meta.env.VITE_CLOUD_API_URL || ''

function mapBoundaryConditions(boundaryConditions: BoundaryCondition[]) {
  return boundaryConditions.map((bc) => ({
    id: bc.id,
    name: bc.name,
    bc_type: bc.type,
    application_method: 'face_ids',
    face_ids: bc.selectionIds || [],
    active: true,
    visible: true,
    color: '#4fc3f7',
    fix_x: bc.type === 'fixation' ? (bc.fixedDofs || []).includes('x') : undefined,
    fix_y: bc.type === 'fixation' ? (bc.fixedDofs || []).includes('y') : undefined,
    fix_z: bc.type === 'fixation' ? (bc.fixedDofs || []).includes('z') : undefined,
    direction: bc.type === 'force'
      ? {
          x: bc.forceVector?.[0] || 0,
          y: bc.forceVector?.[1] || 0,
          z: bc.forceVector?.[2] || 0,
        }
      : undefined,
    magnitude:
      bc.type === 'force'
        ? Math.hypot(bc.forceVector?.[0] || 0, bc.forceVector?.[1] || 0, bc.forceVector?.[2] || 0)
        : bc.pressureValue,
    temperature: bc.type === 'temperature' ? bc.temperatureValue : undefined,
  }))
}

export default function OptimizationPanel() {
  const {
    model,
    boundaryConditions,
    setOptimizationResult,
    optimizationResult,
    isOptimizing,
    setIsOptimizing,
  } = useStore()

  const [mode, setMode] = useState<ExecutionMode>('local')
  const [device, setDevice] = useState<ComputeDevice>('cpu')
  const [workers, setWorkers] = useState(Math.max(1, Math.min(8, Math.floor((navigator.hardwareConcurrency || 4) / 2))))
  const [params, setParams] = useState({ volumeFraction: 0.4, penalty: 3.0, filterRadius: 1.5, maxIterations: 80, tolerance: 1e-4 })
  const [progress, setProgress] = useState<{ iteration: number; compliance: number; change: number } | null>(null)
  const [activeBaseUrl, setActiveBaseUrl] = useState('')
  const pollingRef = useRef<number | null>(null)

  const supportsGPU = useMemo(() => typeof navigator !== 'undefined' && 'gpu' in navigator, [])

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        window.clearInterval(pollingRef.current)
      }
    }
  }, [])

  const stopPolling = () => {
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  const runOptimization = async () => {
    if (mode !== 'local' && !model) return toast.error('Bitte zuerst eine Geometrie laden')
    if (boundaryConditions.length === 0) return toast.error('Bitte mindestens eine Randbedingung definieren')

    stopPolling()
    setProgress(null)

    try {
      if (mode === 'local') {
        setIsOptimizing(true)

        if (device === 'gpu' && !supportsGPU) toast('WebGPU nicht verfügbar, CPU-Fallback aktiv')

        const result = await runLocalOptimization(
          { volumeFraction: params.volumeFraction, penalty: params.penalty, maxIterations: params.maxIterations, device, workers },
          (p) => setProgress(p),
        )

        const localId = crypto.randomUUID()
        setOptimizationResult({
          job_id: localId,
          status: 'completed-local',
          result: { final_compliance: result.compliance, iterations: result.iterations },
        })

        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `local-optimization-${localId}.json`
        link.click()
        URL.revokeObjectURL(url)
        toast.success('Lokale Optimierung abgeschlossen')
        setIsOptimizing(false)
        return
      }

      if (mode === 'cloud' && !CLOUD_API_URL) return toast.error('Cloud-Modus benötigt VITE_CLOUD_API_URL')

      setIsOptimizing(true)
      const baseURL = mode === 'cloud' ? CLOUD_API_URL : ''
      setActiveBaseUrl(baseURL)

      const requestBody = {
        file_id: model!.fileId,
        boundary_conditions: { conditions: mapBoundaryConditions(boundaryConditions) },
        volume_fraction: params.volumeFraction,
        penalty: params.penalty,
        filter_radius: params.filterRadius,
        max_iterations: params.maxIterations,
        tolerance: params.tolerance,
      }

      const { data } = await api.post('/api/optimization/run', requestBody, baseURL ? { baseURL } : undefined)
      setOptimizationResult(data)
      toast.success(mode === 'cloud' ? 'Cloud-Job gestartet' : 'Server-Job gestartet')

      pollingRef.current = window.setInterval(async () => {
        try {
          const statusResponse = await api.get(`/api/optimization/${data.job_id}/status`, baseURL ? { baseURL } : undefined)
          const status = statusResponse.data
          setProgress({ iteration: status.iteration, compliance: status.compliance, change: status.change })
          setOptimizationResult({
            job_id: data.job_id,
            status: status.status,
            result: { final_compliance: status.compliance, iterations: status.iteration },
          })

          if (['completed', 'failed', 'cancelled'].includes(status.status)) {
            stopPolling()
            setIsOptimizing(false)
            if (status.status === 'completed') toast.success('Optimierung abgeschlossen')
            if (status.status === 'failed') toast.error(status.message || 'Optimierung fehlgeschlagen')
            if (status.status === 'cancelled') toast('Optimierung abgebrochen')
          }
        } catch {
          stopPolling()
          setIsOptimizing(false)
        }
      }, 2000)
    } catch (error) {
      console.error(error)
      setIsOptimizing(false)
      toast.error('Optimierung fehlgeschlagen')
    }
  }

  const resultDownloadHref =
    optimizationResult?.job_id && !optimizationResult.status.includes('local')
      ? `${activeBaseUrl}/api/optimization/${optimizationResult.job_id}/result/download`
      : null

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-200">Optimierung</h3>
      <div className="grid grid-cols-3 gap-2 text-xs">
        {(['local', 'server', 'cloud'] as const).map((m) => (
          <button key={m} onClick={() => setMode(m)} className={`py-1.5 rounded ${mode === m ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'}`}>{m.toUpperCase()}</button>
        ))}
      </div>

      {mode === 'local' && (
        <div className="space-y-2 rounded bg-slate-800/60 p-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button onClick={() => setDevice('cpu')} className={`py-1 rounded ${device === 'cpu' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300'}`}>CPU</button>
            <button onClick={() => setDevice('gpu')} className={`py-1 rounded ${device === 'gpu' ? 'bg-violet-600 text-white' : 'bg-slate-700 text-slate-300'}`}>GPU</button>
          </div>
          <p className="text-[11px] text-slate-400">WebGPU: {supportsGPU ? 'verfügbar' : 'nicht verfügbar'}</p>
          <label className="text-xs text-slate-300 block">Threads/Worker: {workers}
            <input type="range" min={1} max={16} step={1} value={workers} onChange={(e) => setWorkers(Number(e.target.value))} className="w-full" />
          </label>
        </div>
      )}

      <label className="text-xs text-slate-300 block">Volumenfraktion: {params.volumeFraction}
        <input type="range" min={0.1} max={0.9} step={0.05} value={params.volumeFraction} onChange={(e) => setParams((p) => ({ ...p, volumeFraction: Number(e.target.value) }))} className="w-full" />
      </label>
      <label className="text-xs text-slate-300 block">Iterationen: {params.maxIterations}
        <input type="range" min={10} max={250} step={10} value={params.maxIterations} onChange={(e) => setParams((p) => ({ ...p, maxIterations: Number(e.target.value) }))} className="w-full" />
      </label>

      <button onClick={runOptimization} disabled={isOptimizing || (mode !== 'local' && !model)} className="w-full py-2 rounded bg-blue-600 disabled:bg-slate-600">
        {isOptimizing ? 'Läuft...' : 'Optimierung starten'}
      </button>

      {progress && <p className="text-xs text-slate-400">Fortschritt: Iteration {progress.iteration}, Compliance {progress.compliance.toFixed(2)}, Δ {progress.change.toFixed(4)}</p>}
      {optimizationResult && <p className="text-xs text-slate-300">Job: {optimizationResult.job_id} ({optimizationResult.status})</p>}
      {resultDownloadHref && (
        <a href={resultDownloadHref} target="_blank" rel="noreferrer" className="block text-xs text-emerald-400 underline">Ergebnis (STL) herunterladen</a>
      )}

      <a href="/topo-opt-standalone.html" target="_blank" rel="noreferrer" className="block text-xs text-blue-400 underline">Standalone HTML ohne Server öffnen</a>
    </div>
  )
}
