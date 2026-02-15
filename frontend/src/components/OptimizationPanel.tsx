import { useState } from 'react'
import { Play, Square, Download, BarChart3 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useStore } from '../store/useStore'
import { api } from '../utils/api'

export default function OptimizationPanel() {
  const { geometry, boundaryConditions, optimizationResult, setOptimizationResult } = useStore()
  const [isRunning, setIsRunning] = useState(false)
  const [params, setParams] = useState({
    volumeFraction: 0.4,
    penalty: 3.0,
    filterRadius: 1.5,
    maxIterations: 200,
    meshResolution: 30,
  })

  const runOptimization = async () => {
    if (!geometry) {
      toast.error('Bitte zuerst eine Geometrie laden')
      return
    }

    if (boundaryConditions.length === 0) {
      toast.error('Bitte mindestens eine Randbedingung definieren')
      return
    }

    setIsRunning(true)
    toast.loading('Optimierung läuft...', { id: 'optimize' })

    try {
      const { data } = await api.post('/api/optimization/run', {
        geometry_id: geometry.id,
        boundary_conditions: boundaryConditions.map(bc => ({
          type: bc.type,
          name: bc.name,
          selection_type: bc.selectionType,
          selection_ids: bc.selectionIds,
          force_vector: bc.forceVector,
          pressure_value: bc.pressureValue,
          temperature_value: bc.temperatureValue,
          fixed_dofs: bc.fixedDofs,
        })),
        volume_fraction: params.volumeFraction,
        penalty: params.penalty,
        filter_radius: params.filterRadius,
        max_iterations: params.maxIterations,
        mesh_resolution: params.meshResolution,
      })

      setOptimizationResult(data)
      toast.success('Optimierung abgeschlossen!', { id: 'optimize' })
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Optimierung fehlgeschlagen', { id: 'optimize' })
    } finally {
      setIsRunning(false)
    }
  }

  const downloadResult = async () => {
    if (!optimizationResult?.job_id) return
    window.open(`/api/optimization/${optimizationResult.job_id}/result/download`, '_blank')
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-200">Optimierungsparameter</h3>

      {/* Parameters */}
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="text-xs text-slate-400 flex justify-between">
            <span>Volumenfraktion</span>
            <span className="text-slate-200">{params.volumeFraction}</span>
          </label>
          <input
            type="range"
            min={0.05} max={0.95} step={0.05}
            value={params.volumeFraction}
            onChange={e => setParams(p => ({ ...p, volumeFraction: parseFloat(e.target.value) }))}
            className="w-full accent-blue-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-slate-400 flex justify-between">
            <span>Penalty (p)</span>
            <span className="text-slate-200">{params.penalty}</span>
          </label>
          <input
            type="range"
            min={1} max={5} step={0.5}
            value={params.penalty}
            onChange={e => setParams(p => ({ ...p, penalty: parseFloat(e.target.value) }))}
            className="w-full accent-blue-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-slate-400 flex justify-between">
            <span>Filterradius</span>
            <span className="text-slate-200">{params.filterRadius}</span>
          </label>
          <input
            type="range"
            min={0.5} max={5} step={0.5}
            value={params.filterRadius}
            onChange={e => setParams(p => ({ ...p, filterRadius: parseFloat(e.target.value) }))}
            className="w-full accent-blue-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-slate-400 flex justify-between">
            <span>Max. Iterationen</span>
            <span className="text-slate-200">{params.maxIterations}</span>
          </label>
          <input
            type="range"
            min={10} max={500} step={10}
            value={params.maxIterations}
            onChange={e => setParams(p => ({ ...p, maxIterations: parseInt(e.target.value) }))}
            className="w-full accent-blue-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-slate-400 flex justify-between">
            <span>Mesh-Auflösung</span>
            <span className="text-slate-200">{params.meshResolution}</span>
          </label>
          <input
            type="range"
            min={10} max={100} step={5}
            value={params.meshResolution}
            onChange={e => setParams(p => ({ ...p, meshResolution: parseInt(e.target.value) }))}
            className="w-full accent-blue-500"
          />
        </div>
      </div>

      {/* Run Button */}
      <button
        onClick={runOptimization}
        disabled={isRunning || !geometry}
        className={`w-full py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors ${
          isRunning
            ? 'bg-red-600 hover:bg-red-500 text-white'
            : 'bg-blue-600 hover:bg-blue-500 text-white disabled:bg-slate-600 disabled:text-slate-400'
        }`}
      >
        {isRunning ? (
          <>
            <Square size={16} />
            Optimierung läuft...
          </>
        ) : (
          <>
            <Play size={16} />
            Optimierung starten
          </>
        )}
      </button>

      {/* Result */}
      {optimizationResult?.result && (
        <div className="bg-slate-700/50 rounded-lg p-3 space-y-2">
          <h4 className="text-sm font-medium text-slate-200 flex items-center gap-2">
            <BarChart3 size={14} className="text-green-400" />
            Ergebnis
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
            <div>Compliance: <span className="text-slate-200">{optimizationResult.result.final_compliance?.toFixed(4)}</span></div>
            <div>Iterationen: <span className="text-slate-200">{optimizationResult.result.iterations}</span></div>
          </div>
          <button
            onClick={downloadResult}
            className="w-full py-1.5 rounded text-xs bg-green-600 hover:bg-green-500 text-white flex items-center justify-center gap-1.5 transition-colors"
          >
            <Download size={12} />
            Ergebnis herunterladen (STL)
          </button>
        </div>
      )}
    </div>
  )
}
