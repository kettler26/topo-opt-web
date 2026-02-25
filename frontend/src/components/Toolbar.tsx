import { useModelStore } from '../store/useStore'

interface ToolbarProps {
  sidebarOpen: boolean
  onToggleSidebar: () => void
}

export default function Toolbar({ sidebarOpen, onToggleSidebar }: ToolbarProps) {
  const { model, setModel, setMeshData, viewMode, setViewMode, showGrid, setShowGrid, showAxes, setShowAxes, isOptimizing } = useModelStore()

  const handleImport = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.stl,.obj,.gltf,.glb,.step,.stp'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch('/api/geometry/upload', { method: 'POST', body: formData })
        if (!response.ok) throw new Error('Upload fehlgeschlagen')
        const result = await response.json()

        setModel({
          fileId: result.file_id,
          filename: result.filename,
          format: result.format,
          meshInfo: result.mesh_info,
          geometryUrl: `/api/geometry/${result.file_id}/download`,
          namedSelections: result.named_selections || [],
        })

        const meshResponse = await fetch(`/api/geometry/${result.file_id}/mesh`)
        if (meshResponse.ok) {
          const mesh = await meshResponse.json()
          setMeshData(mesh)
        }
      } catch (err) {
        console.error('Import failed:', err)
        alert('Import fehlgeschlagen. Bitte Format prüfen.')
      }
    }
    input.click()
  }

  const handleExport = async (format: string) => {
    if (!model) return
    try {
      const response = await fetch(`/api/geometry/${model.fileId}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_format: format }),
      })
      const data = await response.json()

      // Download the exported file
      const link = document.createElement('a')
      link.href = data.download_url
      link.download = `${model.filename.split('.')[0]}_export.${format}`
      link.click()
    } catch (err) {
      console.error('Export failed:', err)
      alert('Export fehlgeschlagen.')
    }
  }

  return (
    <div className="h-12 bg-gray-800 border-b border-gray-700 flex items-center px-4 gap-2">
      <button onClick={onToggleSidebar} className="p-2 hover:bg-gray-700 rounded text-gray-300"
        title={sidebarOpen ? 'Sidebar schließen' : 'Sidebar öffnen'}>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className="w-px h-6 bg-gray-600" />

      {/* Import */}
      <button onClick={handleImport}
        className="px-3 py-1.5 bg-topo-600 hover:bg-topo-700 rounded text-sm font-medium transition-colors">
        📂 Importieren
      </button>

      {/* Export dropdown */}
      {model && (
        <div className="relative group">
          <button className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition-colors text-gray-200">
            💾 Exportieren ▾
          </button>
          <div className="absolute left-0 top-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl hidden group-hover:block z-50 min-w-[140px]">
            {['stl', 'obj', 'glb', 'step'].map(fmt => (
              <button key={fmt} onClick={() => handleExport(fmt)}
                className="block w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg">
                .{fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="w-px h-6 bg-gray-600" />

      {/* View mode */}
      <div className="flex gap-1">
        {(['solid', 'wireframe', 'solid+wireframe'] as const).map((mode) => (
          <button key={mode} onClick={() => setViewMode(mode)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              viewMode === mode ? 'bg-topo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}>
            {mode === 'solid' ? '■ Solid' : mode === 'wireframe' ? '▤ Wire' : '■▤ Beides'}
          </button>
        ))}
      </div>

      <div className="w-px h-6 bg-gray-600" />

      {/* View toggles */}
      <button onClick={() => setShowGrid(!showGrid)}
        className={`px-2 py-1 rounded text-xs transition-colors ${showGrid ? 'bg-gray-600 text-gray-200' : 'bg-gray-700 text-gray-500'}`}>
        ▦ Grid
      </button>
      <button onClick={() => setShowAxes(!showAxes)}
        className={`px-2 py-1 rounded text-xs transition-colors ${showAxes ? 'bg-gray-600 text-gray-200' : 'bg-gray-700 text-gray-500'}`}>
        ✛ Achsen
      </button>

      <div className="flex-1" />

      {isOptimizing && (
        <span className="text-xs text-yellow-400 animate-pulse mr-3">⏳ Optimierung läuft...</span>
      )}

      <span className="text-sm font-bold text-topo-400">🏗️ Topo-Opt-Web v0.2</span>
    </div>
  )
}
