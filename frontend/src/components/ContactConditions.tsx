import { useState } from 'react'
import { useModelStore } from '../store/useStore'

interface ContactPair {
  id: string
  name: string
  contactType: 'bonded' | 'frictionless' | 'frictional' | 'no_separation'
  masterSelectionId: string
  slaveSelectionId: string
  frictionCoefficient: number
  active: boolean
  visible: boolean
  color: string
}

const CONTACT_TYPES = [
  { value: 'bonded', label: 'Verbunden (Bonded)', desc: 'Flächen verklebt, keine Relativbewegung' },
  { value: 'frictionless', label: 'Reibungsfrei', desc: 'Gleiten ohne Reibung' },
  { value: 'frictional', label: 'Reibung', desc: 'Gleiten mit Reibungskoeffizient' },
  { value: 'no_separation', label: 'Keine Trennung', desc: 'Gleiten möglich, aber kein Abheben' },
] as const

export default function ContactConditions() {
  const { model } = useModelStore()
  const [contacts, setContacts] = useState<ContactPair[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (!model) {
    return (
      <div className="text-center text-gray-400 py-8 text-sm">
        Erst ein Modell laden.
      </div>
    )
  }

  const addContact = () => {
    const newContact: ContactPair = {
      id: crypto.randomUUID(),
      name: `Kontakt ${contacts.length + 1}`,
      contactType: 'bonded',
      masterSelectionId: '',
      slaveSelectionId: '',
      frictionCoefficient: 0.2,
      active: true,
      visible: true,
      color: '#ffa726',
    }
    setContacts([...contacts, newContact])
    setExpandedId(newContact.id)
  }

  const removeContact = (id: string) => {
    setContacts(contacts.filter(c => c.id !== id))
    if (expandedId === id) setExpandedId(null)
  }

  const updateContact = (id: string, updates: Partial<ContactPair>) => {
    setContacts(contacts.map(c => c.id === id ? { ...c, ...updates } : c))
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">Kontaktbedingungen</h3>
      <p className="text-xs text-gray-400">
        Definiere Kontakte zwischen Oberflächen. Nutze Named Selections als Master/Slave-Flächen.
      </p>

      <button onClick={addContact}
        className="w-full px-3 py-2 bg-orange-600/20 hover:bg-orange-600/30 border border-orange-600/50 rounded text-xs font-medium text-orange-300 transition-colors">
        ➕ Kontakt hinzufügen
      </button>

      {contacts.length === 0 ? (
        <p className="text-xs text-gray-500 text-center py-4">
          Noch keine Kontakte definiert.
        </p>
      ) : (
        <div className="space-y-2">
          {contacts.map((contact) => (
            <div key={contact.id} className="bg-gray-900 rounded-lg border border-gray-700">
              {/* Header */}
              <div className="flex items-center justify-between p-3 cursor-pointer"
                onClick={() => setExpandedId(expandedId === contact.id ? null : contact.id)}>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: contact.color }} />
                  <span className="text-sm font-medium text-gray-200">{contact.name}</span>
                  <span className="text-xs text-gray-400 capitalize">
                    ({CONTACT_TYPES.find(t => t.value === contact.contactType)?.label})
                  </span>
                </div>
                <div className="flex gap-1">
                  <button onClick={(e) => { e.stopPropagation(); updateContact(contact.id, { active: !contact.active }) }}
                    className={`text-xs px-1 ${contact.active ? 'text-green-400' : 'text-gray-600'}`}>
                    {contact.active ? '✓' : '✗'}
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); removeContact(contact.id) }}
                    className="text-xs text-red-400 hover:text-red-300 px-1">✕</button>
                </div>
              </div>

              {/* Expanded details */}
              {expandedId === contact.id && (
                <div className="px-3 pb-3 space-y-3 border-t border-gray-700 pt-3">
                  {/* Name */}
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Name</label>
                    <input value={contact.name}
                      onChange={(e) => updateContact(contact.id, { name: e.target.value })}
                      className="w-full bg-gray-800 text-sm text-gray-200 px-2 py-1 rounded border border-gray-600" />
                  </div>

                  {/* Contact type */}
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Kontakttyp</label>
                    <select value={contact.contactType}
                      onChange={(e) => updateContact(contact.id, { contactType: e.target.value as ContactPair['contactType'] })}
                      className="w-full bg-gray-800 text-sm text-gray-200 px-2 py-1 rounded border border-gray-600">
                      {CONTACT_TYPES.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {CONTACT_TYPES.find(t => t.value === contact.contactType)?.desc}
                    </p>
                  </div>

                  {/* Master/Slave */}
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Master-Fläche (Named Selection)</label>
                    <input value={contact.masterSelectionId}
                      onChange={(e) => updateContact(contact.id, { masterSelectionId: e.target.value })}
                      placeholder="Selection-ID..."
                      className="w-full bg-gray-800 text-sm text-gray-200 px-2 py-1 rounded border border-gray-600" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Slave-Fläche (Named Selection)</label>
                    <input value={contact.slaveSelectionId}
                      onChange={(e) => updateContact(contact.id, { slaveSelectionId: e.target.value })}
                      placeholder="Selection-ID..."
                      className="w-full bg-gray-800 text-sm text-gray-200 px-2 py-1 rounded border border-gray-600" />
                  </div>

                  {/* Friction coefficient */}
                  {contact.contactType === 'frictional' && (
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">Reibungskoeffizient</span>
                        <span className="text-gray-200">{contact.frictionCoefficient.toFixed(2)}</span>
                      </div>
                      <input type="range" min={0} max={2} step={0.01}
                        value={contact.frictionCoefficient}
                        onChange={(e) => updateContact(contact.id, { frictionCoefficient: parseFloat(e.target.value) })}
                        className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500" />
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
