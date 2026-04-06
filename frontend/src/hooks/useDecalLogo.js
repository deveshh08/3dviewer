import { useEffect, useRef } from 'react'
import { useThree } from '@react-three/fiber'
import * as THREE from 'three'
import { DecalGeometry } from 'three/examples/jsm/geometries/DecalGeometry.js'
import { findBodyMesh, getZoneConfig } from '../utils/findMeshByMaterial'

function prepareGeometry(mesh) {
  let geo = mesh.geometry.clone()
  if (geo.index) geo = geo.toNonIndexed()
  if (!geo.attributes.normal) geo.computeVertexNormals()
  const tmp = new THREE.Mesh(geo, mesh.material)
  tmp.matrixWorld.copy(mesh.matrixWorld)
  tmp.matrixWorldNeedsUpdate = false
  return tmp
}

export function useDecalLogo(glbScene, logoUrl, zone, transform) {
  // Add decal to the R3F root scene so world-space positions are correct
  const { scene: rootScene } = useThree()
  const decalMeshRef = useRef(null)
  const textureRef   = useRef(null)

  useEffect(() => {
    // Cleanup previous decal
    if (decalMeshRef.current) {
      rootScene.remove(decalMeshRef.current)
      decalMeshRef.current.geometry.dispose()
      decalMeshRef.current.material.dispose()
      decalMeshRef.current = null
    }
    if (textureRef.current) {
      textureRef.current.dispose()
      textureRef.current = null
    }

    if (!glbScene || !logoUrl) return

    // Force world matrices to be current before raycasting
    glbScene.updateWorldMatrix(true, true)

    const bodyMesh = findBodyMesh(glbScene)
    if (!bodyMesh) {
      console.warn('[DecalLogo] Could not find a body mesh in the GLB scene.')
      return
    }

    // Prepare geometry for DecalGeometry (non-indexed + normals)
    const decalReadyMesh = prepareGeometry(bodyMesh)

    // Compute bounding box in world space
    const bbox   = new THREE.Box3().setFromObject(bodyMesh)
    const center = bbox.getCenter(new THREE.Vector3())
    const size   = bbox.getSize(new THREE.Vector3())
    console.log('[DecalLogo] center:', center, '| size:', size)

    const zoneConfig = getZoneConfig(zone)

    if (zone === 'back_center') {
      zoneConfig.rayOrigin.set(center.x, center.y + size.y * 0.10, center.z - size.z * 3.0)
      zoneConfig.rayDirection.set(0, 0, 1)
      zoneConfig.fallback.set(center.x, center.y + size.y * 0.10, center.z - size.z * 0.45)
    } else {
      const xOffset = zone === 'chest_left' ? -size.x * 0.15 : size.x * 0.15
      zoneConfig.rayOrigin.set(center.x + xOffset, center.y + size.y * 0.10, center.z + size.z * 3.0)
      zoneConfig.rayDirection.set(0, 0, -1)
      zoneConfig.fallback.set(center.x + xOffset, center.y + size.y * 0.10, center.z + size.z * 0.45)
    }

    const baseDecalScale = Math.min(size.x, size.y) * 0.25

    const raycaster = new THREE.Raycaster(
      zoneConfig.rayOrigin,
      zoneConfig.rayDirection.clone().normalize()
    )
    const hits = raycaster.intersectObject(decalReadyMesh, false)
    console.log('[DecalLogo] Raycast hits:', hits.length, hits[0]?.point)

    let decalPosition, decalNormal
    if (hits.length > 0) {
      decalPosition = hits[0].point.clone()
      decalNormal   = hits[0].face.normal.clone().transformDirection(bodyMesh.matrixWorld)
    } else {
      console.warn('[DecalLogo] Raycast missed — using fallback for zone:', zone)
      decalPosition = zoneConfig.fallback.clone()
      decalNormal   = zone === 'back_center'
        ? new THREE.Vector3(0, 0, -1)
        : new THREE.Vector3(0, 0, 1)
    }

    // Apply user offsets along the surface
    const up     = new THREE.Vector3(0, 1, 0)
    const right  = new THREE.Vector3().crossVectors(decalNormal, up).normalize()
    const trueUp = new THREE.Vector3().crossVectors(right, decalNormal).normalize()
    decalPosition.addScaledVector(right,   transform.offsetX * baseDecalScale * 0.8)
    decalPosition.addScaledVector(trueUp,  transform.offsetY * baseDecalScale * 0.8)

    const quaternion  = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), decalNormal)
    const orientation = new THREE.Euler().setFromQuaternion(quaternion)
    orientation.z    += THREE.MathUtils.degToRad(transform.rotate)

    const decalSize = new THREE.Vector3().setScalar(baseDecalScale * transform.scale)

    let geometry
    try {
      geometry = new DecalGeometry(decalReadyMesh, decalPosition, orientation, decalSize)
    } catch (err) {
      console.error('[DecalLogo] DecalGeometry failed:', err)
      decalReadyMesh.geometry.dispose()
      return
    }
    decalReadyMesh.geometry.dispose()

    const loader = new THREE.TextureLoader()
    loader.load(
      logoUrl,
      (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace
        textureRef.current = texture

        const material = new THREE.MeshStandardMaterial({
          map:                 texture,
          transparent:         true,
          alphaTest:           0.01,
          depthWrite:          false,
          polygonOffset:       true,
          polygonOffsetFactor: -10,
          polygonOffsetUnits:  -10,
          roughness:           0.85,
          metalness:           0.0,
          side:                THREE.FrontSide,
        })

        const decalMesh = new THREE.Mesh(geometry, material)
        decalMesh.name        = 'LogoDecal'
        decalMesh.renderOrder = 999
        // Add to ROOT scene — positions are in world space
        rootScene.add(decalMesh)
        decalMeshRef.current = decalMesh
        console.log('[DecalLogo] ✅ Decal added at', decalPosition)
      },
      undefined,
      (err) => console.error('[DecalLogo] Texture load failed:', err)
    )

    return () => {
      if (decalMeshRef.current) {
        rootScene.remove(decalMeshRef.current)
        decalMeshRef.current.geometry.dispose()
        decalMeshRef.current.material.dispose()
        decalMeshRef.current = null
      }
      if (textureRef.current) {
        textureRef.current.dispose()
        textureRef.current = null
      }
    }
  }, [rootScene, glbScene, logoUrl, zone, transform])
}
