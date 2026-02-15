import { useState } from 'react'
import { Upload, Settings, Play, Layers, Anchor, ArrowDownToLine } from 'lucide-react'
import FileUpload from './FileUpload'
import BoundaryConditions from './BoundaryConditions'
import OptimizationPanel from './OptimizationPanel'

type Tab = 'geometry' | 'boundary' | 'optimize'

export default function Sidebar() {
  const [activeTab, setActiveTab] = useState<Tab>('geometry')

  const tabs = [
    { id: 'geometry' as Tab, label: 'Geometrie', icon: Layers },
    { id: 'boundary' as Tab, label: 'Randbedingungen', icon: Anchor },
    { id: 'optimize' as Tab, label: 'Optimierung', icon: Play },
  ]

  return (
    <div className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h1 className="text-lg font-bold text-white flex items-center gap-2">
          <span className="text-2xl">🏗️</span>
          TopoOpt Web
        </h1>
        <p className="text-xs text-slate-400 mt-1">Topologie-Optimierung</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 py-2 px-3 text-xs font-medium flex flex-col items-center gap-1 transition-colors ${
              activeTab === id
                ? 'text-blue-400 bg-slate-700/50 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'geometry' && <FileUpload />}
        {activeTab === 'boundary' && <BoundaryConditions />}
        {activeTab === 'optimize' && <OptimizationPanel />}
      </div>
    </div>
  )
}
