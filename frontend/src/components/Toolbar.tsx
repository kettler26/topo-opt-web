import { Download, RotateCcw, Eye, EyeOff, Grid3x3 } from 'lucide-react'
import { useStore } from '../store/useStore'

export default function Toolbar() {
  const { meshData, showWireframe, toggleWireframe } = useStore()

  return (
    <div className="h-10 bg-slate-800 border-b border-slate-700 flex items-center px-4 gap-2">
      {/* View controls */}
      <button
        onClick={toggleWireframe}
        className="flex items-center gap-1.5 px-2 py-1 text-xs rounded hover:bg-slate-700 text-slate-300 transition-colors"
        title={showWireframe ? 'Wireframe ausblenden' : 'Wireframe anzeigen'}
      >
        <Grid3x3 size={14} />
        Wireframe
      </button>

      <div className="flex-1" />

      {/* Status */}
      <span className="text-xs text-slate-500">
        {meshData ? 'Geometrie geladen' : 'Keine Geometrie'}
      </span>

      {/* Export */}
      {meshData && (
        <button className="flex items-center gap-1.5 px-2 py-1 text-xs rounded bg-blue-600 hover:bg-blue-500 text-white transition-colors">
          <Download size={14} />
          Export
        </button>
      )}
    </div>
  )
}
