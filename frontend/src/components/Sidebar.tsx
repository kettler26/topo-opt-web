import { useState } from 'react'
import { useModelStore } from '../store/useStore'
import BoundaryConditions from './BoundaryConditions'
import NamedSelections from './NamedSelections'
import ContactConditions from './ContactConditions'
import OptimizationPanel from './OptimizationPanel'
import MeshRefinement from './MeshRefinement'

type Tab = 'model' | 'selections' | 'bc' | 'contacts' | 'mesh' | 'optimize'

export default function Sidebar() {
  const [activeTab, setActiveTab] = useState<Tab>('model')
  const { model } = useModelStore()

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'model', label: 'Modell', icon: '📐' },
    { id: 'selections', label: 'Selektionen', icon: '🎯' },
    { id: 'bc', label: 'RB', icon: '📌' },
    { id: 'contacts', label: 'Kontakte', icon: '🤝' },
    { id: 'mesh', label: 'Netz', icon: '🔧' },
    { id: 'optimize', label: 'Optim.', icon: '⚡' },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar — scrollable for many tabs */}
      <div className="flex border-b border-gray-700 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-shrink-0 py-2.5 px-2 text-[10px] font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-gray-700 text-topo-400 border-b-2 border-topo-400'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-750'
            }`}
          >
            <span className="block text-center">{tab.icon}</span>
            <span className="block text-center">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'model' && <ModelTab />}
        {activeTab === 'selections' && <NamedSelections />}
        {activeTab === 'bc' && <BoundaryConditions />}
        {activeTab === 'contacts' && <ContactConditions />}
        {activeTab === 'mesh' && <MeshRefinement />}
        {activeTab === 'optimize' && <OptimizationPanel />}
      </div>
    </div>
  )
}

function ModelTab() {
  const { model } = useModelStore()

  if (!model) {
    return (
      <div className="text-center text-gray-400 py-8">
        <p className="text-4xl mb-4">📂</p>
        <p className="text-sm">Keine Geometrie geladen.</p>
        <p className="text-xs mt-2">Nutze \"Importieren\" in der Toolbar.</p>
      </div>
    )
  }

  const info = model.meshInfo as any

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">Modell-Info</h3>
      <div className="space-y-2 text-xs">
        <InfoRow label="Datei" value={model.filename} />
        <InfoRow label="Format" value={model.format} />
        <InfoRow label="Vertices" value={info?.vertices?.toLocaleString() ?? info?.num_vertices?.toLocaleString() ?? '—'} />
        <InfoRow label="Faces" value={info?.faces?.toLocaleString() ?? info?.num_faces?.toLocaleString() ?? '—'} />
        <InfoRow label="Wasserdicht" value={info?.is_watertight ? '✅ Ja' : '❌ Nein'} />
        {info?.volume && <InfoRow label="Volumen" value={`${info.volume.toFixed(4)}`} />}
        {info?.surface_area && <InfoRow label="Oberfläche" value={`${info.surface_area.toFixed(4)}`} />}
      </div>

      {/* STEP-specific info */}
      {info?.solids != null && (
        <div className="mt-4">
          <h4 className="text-xs font-semibold text-gray-300 mb-2">CAD-Topologie</h4>
          <div className="space-y-1 text-xs">
            <InfoRow label="Körper" value={String(info.solids)} />
            <InfoRow label="Flächen" value={String(info.faces)} />
            <InfoRow label="Kanten" value={String(info.edges)} />
            <InfoRow label="Eckpunkte" value={String(info.vertices)} />
          </div>
        </div>
      )}
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-200 font-medium">{value}</span>
    </div>
  )
}
