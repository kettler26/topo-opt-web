import { useState } from 'react'
import { useModelStore } from '../store/useStore'

interface RefinementConfig {
  strategy: 'uniform' | 'adaptive' | 'local' | 'edge_length'
  targetEdgeLength: number
  maxElements: number
  refinementLevel: number
  qualityThreshold: number
}

interface MeshStats {
  numVertices: number
  numFaces: number
  minEdgeLength: number
  maxEdgeLength: number
  meanEdgeLength: number
  meanQuality: number
  poorElements: number
}

export default function MeshRefinement() {
  const { model } = useModelStore()
  const [config, setConfig] = useState<RefinementConfig>({
    strategy: 'uniform',
    targetEdgeLength: 0.5,
    maxElements: 100000,
    refinementLevel: 1,
    qualityThreshold: 0.3,
  })
  const [isRefining, setIsRefining] = useState(false)
  const [stats, setStats] = useState<MeshStats | null>(null)

  if (!model) {
    return (
      <div className="text-center text-gray-400 py-8 text-sm">
        Erst ein Modell laden.
      </div>
    )
  }

  const loadStats = async () => {
    try {
      const res = await fetch(`/api/geometry/${model.fileId}/mesh-stats`)
      const data = await res.json()
      setStats({
        numVertices: data.num_vertices,
        numFaces: data.num_faces,
        minEdgeLength: data.min_edge_length,
        maxEdgeLength: data.max_edge_length,
        meanEdgeLength: data.mean_edge_length,
        meanQuality: data.mean_quality,
        poorElements: data.poor_elements,
      })
    } catch (err) {
      console.error('Stats laden fehlgeschlagen:', err)
    }
  }

  const handleRefine = async () => {
    setIsRefining(true)
    try {
      const res = await fetch(`/api/geometry/${model.fileId}/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy: config.strategy,
          target_edge_length: config.targetEdgeLength,
          max_elements: config.maxElements,
          refinement_level: config.refinementLevel,
          quality_threshold: config.qualityThreshold,
        }),
      })
      const data = await res.json()
      console.log('Refinement result:', data)
      // Update stats with new mesh
      if (data.stats_after) {
        setStats({
          numVertices: data.stats_after.num_vertices,
          numFaces: data.stats_after.num_faces,
          minEdgeLength: data.stats_after.min_edge_length,
          maxEdgeLength: data.stats_after.max_edge_length,
          meanEdgeLength: data.stats_after.mean_edge_length,
          meanQuality: data.stats_after.mean_quality,
          poorElements: data.stats_after.poor_elements,
        })
      }
    } catch (err) {
      console.error('Refinement fehlgeschlagen:', err)
    } finally {
      setIsRefining(false)
    }
  }

  const strategies = [
    { value: 'uniform', label: 'Gleichmäßig', desc: 'Alle Elemente gleich verfeinern' },
    { value: 'adaptive', label: 'Adaptiv', desc: 'Basierend auf Elementqualität' },
    { value: 'edge_length', label: 'Kantenlänge', desc: 'Ziel-Kantenlänge erreichen' },
    { value: 'local', label: 'Lokal', desc: 'Nur ausgewählte Bereiche' },
  ] as const

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">Netzverfeinerung</h3>

      {/* Load stats button */}
      <button onClick={loadStats}
        className="w-full px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-xs font-medium text-gray-200 transition-colors">
        📊 Netzstatistik laden
      </button>

      {/* Stats display */}
      {stats && (
        <div className="bg-gray-900 rounded-lg p-3 space-y-1 text-xs">
          <div className="flex justify-between"><span className="text-gray-400">Knoten</span><span className="text-gray-200">{stats.numVertices.toLocaleString()}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Elemente</span><span className="text-gray-200">{stats.numFaces.toLocaleString()}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Ø Kantenlänge</span><span className="text-gray-200">{stats.meanEdgeLength.toFixed(4)}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Min/Max Kantenlänge</span><span className="text-gray-200">{stats.minEdgeLength.toFixed(4)} / {stats.maxEdgeLength.toFixed(4)}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Ø Qualität</span><span className="text-gray-200">{stats.meanQuality.toFixed(3)}</span></div>
          <div className="flex justify-between">
            <span className="text-gray-400">Schlechte Elemente</span>
            <span className={stats.poorElements > 0 ? 'text-yellow-400' : 'text-green-400'}>
              {stats.poorElements}
            </span>
          </div>
        </div>
      )}

      {/* Strategy selection */}
      <div>
        <label className="text-xs text-gray-400 block mb-1">Strategie</label>
        <div className="grid grid-cols-2 gap-1">
          {strategies.map(s => (
            <button key={s.value}
              onClick={() => setConfig({ ...config, strategy: s.value })}
              className={`px-2 py-1.5 rounded text-xs transition-colors ${
                config.strategy === s.value
                  ? 'bg-topo-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}>
              {s.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {strategies.find(s => s.value === config.strategy)?.desc}
        </p>
      </div>

      {/* Parameters */}
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Verfeinerungsstufe</span>
            <span className="text-gray-200">{config.refinementLevel}</span>
          </div>
          <input type="range" min={1} max={5} step={1} value={config.refinementLevel}
            onChange={(e) => setConfig({ ...config, refinementLevel: parseInt(e.target.value) })}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-topo-500" />
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Max. Elemente</span>
            <span className="text-gray-200">{config.maxElements.toLocaleString()}</span>
          </div>
          <input type="range" min={1000} max={5000000} step={1000} value={config.maxElements}
            onChange={(e) => setConfig({ ...config, maxElements: parseInt(e.target.value) })}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-topo-500" />
        </div>

        {config.strategy === 'edge_length' && (
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-400">Ziel-Kantenlänge</span>
              <span className="text-gray-200">{config.targetEdgeLength.toFixed(3)}</span>
            </div>
            <input type="range" min={0.001} max={10} step={0.001} value={config.targetEdgeLength}
              onChange={(e) => setConfig({ ...config, targetEdgeLength: parseFloat(e.target.value) })}
              className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-topo-500" />
          </div>
        )}
      </div>

      {/* Refine button */}
      <button onClick={handleRefine} disabled={isRefining}
        className={`w-full py-2.5 rounded-lg font-semibold text-sm transition-colors ${
          !isRefining ? 'bg-topo-600 hover:bg-topo-700 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed'
        }`}>
        {isRefining ? '⏳ Verfeinere...' : '🔧 Netz verfeinern'}
      </button>
    </div>
  )
}
