import { useCallback } from 'react'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

/**
 * Hook for loading 3D geometry files directly in the browser.
 * Used as a fallback when the backend is not available.
 */
export function useGeometryLoader() {
  const loadSTL = useCallback((file: File) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const loader = new STLLoader()
          const geometry = loader.parse(e.target?.result as ArrayBuffer)
          resolve(geometry)
        } catch (err) {
          reject(err)
        }
      }
      reader.readAsArrayBuffer(file)
    })
  }, [])

  return { loadSTL }
}
