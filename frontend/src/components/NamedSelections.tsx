import { useState } from 'react'
import { useModelStore } from '../store/useStore'

interface NamedSelection {
  id: string
  name: string
  entityType: 'face' | 'edge' | 'vertex' | 'node'
  entityIndices: number[]
  color: string
  visible: boolean
  locked: boolean
}

export default function NamedSelections() {
  const { model } = useModelStore()
  const [selections, setSelections] = useState<NamedSelection[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)

  if (!model) {
    return (
      <div className="text-center text-gray-400 py-8 text-sm">
        Erst ein Modell laden.
      </div>
    )
  }

  const addSelection = (type: NamedSelection['entityType']) => {
    const colors = ['#ff6b6b', '#ffa726', '#66bb6a', '#42a5f5', '#ab47bc', '#26c6da']
    const newSel: NamedSelection = {
      id: crypto.randomUUID(),
      name: `Selektion ${selections.length + 1}`,
      entityType: type,
      entityIndices: [],
      color: colors[selections.length % colors.length],
      visible: true,
      locked: false,
    }
    setSelections([...selections, newSel])
  }

  const removeSelection = (id: string) => {
    setSelections(selections.filter(s => s.id !== id))
  }

  const updateName = (id: string, name: string) => {
    setSelections(selections.map(s => s.id === id ? { ...s, name } : s))
    setEditingId(null)
  }

  const toggleVisibility = (id: string) => {
    setSelections(selections.map(s => s.id === id ? { ...s, visible: !s.visible } : s))
  }

  const toggleLock = (id: string) => {
    setSelections(selections.map(s => s.id === id ? { ...s, locked: !s.locked } : s))
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">Named Selections</h3>
      <p className="text-xs text-gray-400">
        Erstelle benannte Selektionen um Flächen, Kanten oder Knoten zu gruppieren.
        Diese können dann für Randbedingungen und Kontakte verwendet werden.
      </p>

      {/* Add buttons */}
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => addSelection('face')}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-xs font-medium text-gray-200 transition-colors">
          🔲 Flächen
        </button>
        <button onClick={() => addSelection('edge')}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-xs font-medium text-gray-200 transition-colors">
          📏 Kanten
        </button>
        <button onClick={() => addSelection('vertex')}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-xs font-medium text-gray-200 transition-colors">
          📍 Knoten
        </button>
        <button onClick={() => addSelection('node')}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-xs font-medium text-gray-200 transition-colors">
          🔴 Netzknoten
        </button>
      </div>

      {/* Info box */}
      <div className="bg-blue-900/20 border border-blue-800 rounded p-3 text-xs text-blue-300">
        💡 Klicke auf Flächen im 3D-Viewer um sie zur aktiven Selektion hinzuzufügen.
      </div>

      {/* Selection list */}
      {selections.length === 0 ? (
        <p className="text-xs text-gray-500 text-center py-4">
          Noch keine Selektionen erstellt.
        </p>
      ) : (
        <div className="space-y-2">
          {selections.map((sel) => (
            <div key={sel.id}
              className="bg-gray-900 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sel.color }} />
                  {editingId === sel.id ? (
                    <input
                      autoFocus
                      defaultValue={sel.name}
                      onBlur={(e) => updateName(sel.id, e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && updateName(sel.id, (e.target as HTMLInputElement).value)}
                      className="bg-gray-800 text-sm text-gray-200 px-2 py-0.5 rounded border border-gray-600 w-32"
                    />
                  ) : (
                    <span className="text-sm font-medium text-gray-200 cursor-pointer"
                      onDoubleClick={() => setEditingId(sel.id)}>
                      {sel.name}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={() => toggleVisibility(sel.id)}
                    className={`p-1 rounded text-xs ${sel.visible ? 'text-gray-300' : 'text-gray-600'}`}>
                    {sel.visible ? '👁️' : '👁️‍🗨️'}
                  </button>
                  <button onClick={() => toggleLock(sel.id)}
                    className={`p-1 rounded text-xs ${sel.locked ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {sel.locked ? '🔒' : '🔓'}
                  </button>
                  <button onClick={() => removeSelection(sel.id)}
                    className="p-1 rounded text-xs text-red-400 hover:text-red-300">
                    ✕
                  </button>
                </div>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span className="capitalize">{sel.entityType === 'face' ? 'Flächen' : sel.entityType === 'edge' ? 'Kanten' : sel.entityType === 'vertex' ? 'Knoten' : 'Netzknoten'}</span>
                <span>{sel.entityIndices.length} ausgewählt</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
