import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useStore } from '../store/useStore'
import { api } from '../utils/api'

export default function FileUpload() {
  const { geometry, setGeometry, setMeshData } = useStore()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      toast.loading('Geometrie wird hochgeladen...', { id: 'upload' })

      const { data: geo } = await api.post('/api/geometry/upload', formData)
      setGeometry(geo)

      // Load mesh data for viewer
      const { data: mesh } = await api.get(`/api/geometry/${geo.id}/mesh`)
      setMeshData(mesh)

      toast.success(`${file.name} erfolgreich geladen`, { id: 'upload' })
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload fehlgeschlagen', { id: 'upload' })
    }
  }, [setGeometry, setMeshData])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'model/stl': ['.stl'],
      'model/obj': ['.obj'],
      'model/gltf+json': ['.gltf'],
      'model/gltf-binary': ['.glb'],
    },
    maxFiles: 1,
  })

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-200">Geometrie importieren</h3>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-400 bg-blue-400/10'
            : 'border-slate-600 hover:border-slate-500 hover:bg-slate-700/30'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-2 text-slate-400" size={24} />
        <p className="text-sm text-slate-300">
          {isDragActive ? 'Datei hier ablegen...' : 'Datei hierher ziehen oder klicken'}
        </p>
        <p className="text-xs text-slate-500 mt-1">STL, OBJ, glTF, GLB</p>
      </div>

      {/* Loaded geometry info */}
      {geometry && (
        <div className="bg-slate-700/50 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <File size={14} className="text-blue-400" />
              <span className="text-sm text-slate-200 truncate">{geometry.filename}</span>
            </div>
            <button
              onClick={() => {
                setGeometry(null)
                setMeshData(null)
              }}
              className="text-slate-400 hover:text-red-400 transition-colors"
            >
              <Trash2 size={14} />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
            <div>Vertices: <span className="text-slate-200">{geometry.vertices_count?.toLocaleString()}</span></div>
            <div>Faces: <span className="text-slate-200">{geometry.faces_count?.toLocaleString()}</span></div>
            <div>Format: <span className="text-slate-200">{geometry.format}</span></div>
            {geometry.volume && (
              <div>Volumen: <span className="text-slate-200">{geometry.volume.toFixed(2)}</span></div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
