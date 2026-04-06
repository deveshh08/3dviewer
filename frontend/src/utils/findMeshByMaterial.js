import * as THREE from 'three'

export function findBodyMesh(root) {
  const highPriority = ['body', 'torso', 'shirt', 'fabric', 'sweatshirt', 'hoodie', 'garment', 'cloth']
  const allMeshes = []

  root.traverse((obj) => {
    if (!obj.isMesh || !obj.geometry) return
    allMeshes.push(obj)
  })

  if (allMeshes.length === 0) return null
  if (allMeshes.length === 1) return allMeshes[0]

  // Try name match first
  for (const mesh of allMeshes) {
    const name = (mesh.name || '').toLowerCase()
    if (highPriority.some(n => name.includes(n))) return mesh
  }

  // Fall back to largest bounding box (almost always the main fabric body)
  let bestMesh = allMeshes[0]
  let bestVol  = 0
  for (const mesh of allMeshes) {
    const box  = new THREE.Box3().setFromObject(mesh)
    const size = box.getSize(new THREE.Vector3())
    const vol  = size.x * size.y * size.z
    if (vol > bestVol) { bestVol = vol; bestMesh = mesh }
  }
  return bestMesh
}

export function getZoneConfig(zone) {
  // These are placeholder values — useDecalLogo overwrites them with
  // bbox-scaled values before use, so the exact numbers here don't matter.
  const configs = {
    chest_left: {
      rayOrigin:    new THREE.Vector3(-0.15, 0.15, 2.0),
      rayDirection: new THREE.Vector3(0, 0, -1),
      fallback:     new THREE.Vector3(-0.15, 0.15, 0.28),
      decalSize:    new THREE.Vector3(0.20, 0.20, 0.20),
    },
    chest_right: {
      rayOrigin:    new THREE.Vector3(0.15, 0.15, 2.0),
      rayDirection: new THREE.Vector3(0, 0, -1),
      fallback:     new THREE.Vector3(0.15, 0.15, 0.28),
      decalSize:    new THREE.Vector3(0.20, 0.20, 0.20),
    },
    back_center: {
      rayOrigin:    new THREE.Vector3(0, 0.05, -2.0),
      rayDirection: new THREE.Vector3(0, 0, 1),
      fallback:     new THREE.Vector3(0, 0.05, -0.28),
      decalSize:    new THREE.Vector3(0.35, 0.35, 0.35),
    },
  }
  return configs[zone] ?? configs['chest_left']
}
