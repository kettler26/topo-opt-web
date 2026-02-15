import { useMemo } from 'react'
import * as THREE from 'three'

interface MeshData {
  vertices: number[][]
  faces: number[][]
  normals?: number[][]
}

interface Props {
  data: MeshData
}

export default function MeshViewer({ data }: Props) {
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()

    // Flatten vertices
    const positions = new Float32Array(data.vertices.flat())
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))

    // Flatten faces
    const indices = new Uint32Array(data.faces.flat())
    geo.setIndex(new THREE.BufferAttribute(indices, 1))

    // Compute normals if not provided
    geo.computeVertexNormals()

    // Center the geometry
    geo.computeBoundingBox()
    const center = new THREE.Vector3()
    geo.boundingBox?.getCenter(center)
    geo.translate(-center.x, -center.y, -center.z)

    return geo
  }, [data])

  return (
    <group>
      {/* Solid mesh */}
      <mesh geometry={geometry}>
        <meshStandardMaterial
          color="#3b82f6"
          metalness={0.1}
          roughness={0.6}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Wireframe overlay */}
      <mesh geometry={geometry}>
        <meshBasicMaterial
          color="#1e40af"
          wireframe
          transparent
          opacity={0.1}
        />
      </mesh>
    </group>
  )
}
