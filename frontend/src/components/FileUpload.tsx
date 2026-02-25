import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useStore } from '../store/useStore'

export default function FileUpload() {
  const { setModel, setMeshData } = useStore()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/geometry/upload', { method: 'POST', body: formData })
    const data = await res.json()
    setModel({ fileId: data.file_id, filename: data.filename, format: data.format, meshInfo: data.mesh_info, geometryUrl: `/api/geometry/${data.file_id}/download`, namedSelections: data.named_selections || [] })
    const meshRes = await fetch(`/api/geometry/${data.file_id}/mesh`)
    if (meshRes.ok) setMeshData(await meshRes.json())
  }, [setModel, setMeshData])

  const { getRootProps, getInputProps } = useDropzone({ onDrop })

  return <div {...getRootProps()} className="p-4 border border-dashed rounded text-xs text-slate-300 cursor-pointer"><input {...getInputProps()} />Datei hier ablegen</div>
}
