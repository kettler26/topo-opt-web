import { useState } from 'react'
import { Plus, Trash2, Lock, ArrowDown, Gauge, Thermometer } from 'lucide-react'
import { useStore } from '../store/useStore'
import type { BoundaryCondition } from '../store/useStore'

const BC_TYPES = [
  { value: 'fixation', label: 'Fixierung', icon: Lock, color: 'text-red-400' },
  { value: 'force', label: 'Kraft', icon: ArrowDown, color: 'text-green-400' },
  { value: 'pressure', label: 'Drucklast', icon: Gauge, color: 'text-yellow-400' },
  { value: 'temperature', label: 'Temperatur', icon: Thermometer, color: 'text-orange-400' },
] as const

export default function BoundaryConditions() {
  const { boundaryConditions, addBoundaryCondition, removeBoundaryCondition, updateBoundaryCondition } = useStore()

  const addBC = (type: string) => {
    const newBC: BoundaryCondition = {
      id: crypto.randomUUID(),
      type: type as BoundaryCondition['type'],
      name: `${BC_TYPES.find(t => t.value === type)?.label || 'BC'} ${boundaryConditions.length + 1}`,
      selectionType: 'faces',
      selectionIds: [],
      forceVector: type === 'force' ? [0, -1000, 0] : undefined,
      pressureValue: type === 'pressure' ? 1000 : undefined,
      temperatureValue: type === 'temperature' ? 300 : undefined,
      fixedDofs: type === 'fixation' ? ['x', 'y', 'z'] : undefined,
    }
    addBoundaryCondition(newBC)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-200">Randbedingungen</h3>

      {/* Add BC buttons */}
      <div className="grid grid-cols-2 gap-2">
        {BC_TYPES.map(({ value, label, icon: Icon, color }) => (
          <button
            key={value}
            onClick={() => addBC(value)}
            className="flex items-center gap-2 px-3 py-2 text-xs bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors text-slate-300"
          >
            <Icon size={14} className={color} />
            + {label}
          </button>
        ))}
      </div>

      {/* BC List */}
      <div className="space-y-2">
        {boundaryConditions.length === 0 && (
          <p className="text-xs text-slate-500 text-center py-4">
            Keine Randbedingungen definiert.\nKlicke oben um welche hinzuzufügen.
          </p>
        )}

        {boundaryConditions.map((bc) => {
          const typeInfo = BC_TYPES.find(t => t.value === bc.type)
          const Icon = typeInfo?.icon || Lock

          return (
            <div key={bc.id} className="bg-slate-700/50 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon size={14} className={typeInfo?.color || 'text-slate-400'} />
                  <input
                    type="text"
                    value={bc.name}
                    onChange={(e) => updateBoundaryCondition(bc.id, { name: e.target.value })}
                    className="bg-transparent text-sm text-slate-200 border-none focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1"
                  />
                </div>
                <button
                  onClick={() => removeBoundaryCondition(bc.id)}
                  className="text-slate-400 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {/* Type-specific fields */}
              {bc.type === 'force' && (
                <div className="grid grid-cols-3 gap-1">
                  {['X', 'Y', 'Z'].map((axis, i) => (
                    <div key={axis} className="space-y-1">
                      <label className="text-xs text-slate-500">F{axis} (N)</label>
                      <input
                        type="number"
                        value={bc.forceVector?.[i] || 0}
                        onChange={(e) => {
                          const newVec = [...(bc.forceVector || [0, 0, 0])]
                          newVec[i] = parseFloat(e.target.value) || 0
                          updateBoundaryCondition(bc.id, { forceVector: newVec })
                        }}
                        className="w-full bg-slate-800 text-xs text-slate-200 px-2 py-1 rounded border border-slate-600 focus:border-blue-400 focus:outline-none"
                      />
                    </div>
                  ))}
                </div>
              )}

              {bc.type === 'pressure' && (
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Druck (Pa)</label>
                  <input
                    type="number"
                    value={bc.pressureValue || 0}
                    onChange={(e) => updateBoundaryCondition(bc.id, { pressureValue: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-800 text-xs text-slate-200 px-2 py-1 rounded border border-slate-600 focus:border-blue-400 focus:outline-none"
                  />
                </div>
              )}

              {bc.type === 'temperature' && (
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Temperatur (K)</label>
                  <input
                    type="number"
                    value={bc.temperatureValue || 0}
                    onChange={(e) => updateBoundaryCondition(bc.id, { temperatureValue: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-800 text-xs text-slate-200 px-2 py-1 rounded border border-slate-600 focus:border-blue-400 focus:outline-none"
                  />
                </div>
              )}

              {bc.type === 'fixation' && (
                <div className="flex gap-2">
                  {['x', 'y', 'z'].map((dof) => (
                    <label key={dof} className="flex items-center gap-1 text-xs text-slate-400">
                      <input
                        type="checkbox"
                        checked={bc.fixedDofs?.includes(dof) || false}
                        onChange={(e) => {
                          const dofs = bc.fixedDofs || []
                          const newDofs = e.target.checked
                            ? [...dofs, dof]
                            : dofs.filter(d => d !== dof)
                          updateBoundaryCondition(bc.id, { fixedDofs: newDofs })
                        }}
                        className="rounded border-slate-600"
                      />
                      {dof.toUpperCase()}
                    </label>
                  ))}
                </div>
              )}

              <p className="text-xs text-slate-500">
                Flächen auswählen: Klicke im 3D-Viewer auf die gewünschten Flächen
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
