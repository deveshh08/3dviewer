# iPromo 3D Configurator — Clarity Guide + Logo Placement Plan

> **This document answers your questions first, then gives the exact code to fix logo placement.**

---

## ❓ Your Questions Answered

### Q1: "What is the need of custom images / 3D?"

**Short answer: You don't need to create any 3D model yourself. You already solved this.**

Here is exactly how the system works:

```
User visits the page
        ↓
App loads the .glb file you downloaded from Sketchfab   ← already working ✅
        ↓
User picks a color → app changes the material color in Three.js  ← already working ✅
        ↓
User uploads their logo (PNG/JPG/SVG)
        ↓
App PROJECTS that logo onto the surface of the 3D model  ← THIS IS WHAT'S MISSING ❌
        ↓
User can rotate the model and see their logo on the fabric
```

The "custom image" confusion came from the earlier plan mentioning a mesh called
`LogoPlane_Chest` — that approach only works if the GLB was built from scratch with
that mesh pre-added. Since you downloaded a real GLB from Sketchfab, that mesh
does NOT exist in your file. We need a completely different technique.

---

### Q2: "Are we going to add manual images and then create 3D?"

**No. Never.** The workflow is:

| What the user provides | What the app does |
|---|---|
| Their logo file (PNG/JPG/SVG) | Loads it as a texture in Three.js |
| Nothing — GLB stays the same | Projects the logo ONTO the existing 3D mesh |

You never rebuild or modify the .glb file. The logo is applied at runtime in the
browser using a technique called **Decal Projection**.

---

### Q3: "The logo placement is not visible on the 3D model — why?"

Because the original plan used `LogoPlane_Chest` — a separate mesh that doesn't
exist in your Sketchfab GLB. When Three.js looks for a mesh with that name and
can't find it, it silently does nothing. No error, no logo.

The fix is **THREE.DecalGeometry** — a built-in Three.js feature that:
1. Takes any existing mesh (the sweatshirt body)
2. Projects your logo texture onto its surface at a position you specify
3. Handles the 3D curvature automatically — the logo wraps around fabric
4. Responds to lighting — looks printed on, not pasted on top

This is the industry-standard technique used by Nike, Under Armour, and every
real apparel configurator.

---

## 🗺️ What Is Already Done vs What Remains

### ✅ Already Working
- GLB loads and renders in Three.js
- OrbitControls (rotate/zoom)
- Basic page layout

### ❌ Still Needs to Be Built
1. **Logo placement with DecalGeometry** ← most important, covered in full below
2. **Color change** — tint the fabric material by hex color
3. **Logo position controls** — sliders for X/Y position and scale
4. **Logo zone selector** — left chest / right chest / back center
5. **Share link** — save config to backend, generate UUID URL
6. **PDF download** — canvas screenshot → ReportLab PDF

---

## 🔧 How THREE.DecalGeometry Works (The Core Concept)

Think of it like a rubber stamp:

```
Your Logo PNG
     ↓
Three.js loads it as a texture
     ↓
You pick a POINT on the sweatshirt surface (e.g. left chest)
     ↓
DecalGeometry creates a thin mesh that HUGS the surface at that point
     ↓
The logo texture is applied to that thin mesh
     ↓
Result: logo appears to be printed/embroidered on the fabric
        it wraps around curves, reacts to light, rotates with the model
```

The key inputs to DecalGeometry are:
- `mesh`     — the sweatshirt mesh object
- `position` — a 3D point (Vector3) on the surface where the logo center goes
- `orientation` — a 3D rotation (Euler) so the logo faces outward from the surface
- `size`     — a Vector3 controlling width × height × depth of the stamp

---

## 📁 File Structure (Only Changed/New Files)

```
frontend/src/
├── components/
│   ├── Viewer3D.jsx            ← REWRITE — add DecalGeometry logic
│   ├── LogoUploader.jsx        ← REWRITE — add zone selector + sliders
│   ├── ColorPicker.jsx         ← minor update
│   └── (rest unchanged)
├── hooks/
│   └── useDecalLogo.js         ← NEW — handles all logo projection logic
├── utils/
│   └── findMeshByMaterial.js   ← NEW — finds the body mesh inside the GLB
└── store/
    └── configuratorStore.js    ← add logoZone + decalTransform fields
```

---

## 📦 Extra Package to Install

```bash
cd frontend
npm install three-stdlib
```

`three-stdlib` gives us `DecalGeometry` pre-built. Alternatively it is available
directly in recent Three.js versions:

```js
import { DecalGeometry } from 'three/examples/jsm/geometries/DecalGeometry.js'
```

No extra install needed if your three version is ≥ 0.150.

---

## 🔑 Step 1 — Update the Zustand Store

### `frontend/src/store/configuratorStore.js`

```js
import { create } from 'zustand'

export const useConfigurator = create((set) => ({
  // ── Product ──────────────────────────────────────────────────
  productUrl:  '',
  productData: null,

  // ── Color ────────────────────────────────────────────────────
  selectedColor: '#7ECECE',

  // ── Logo ─────────────────────────────────────────────────────
  logoTexture: null,      // URL string returned by backend after upload

  // Which zone to stamp the logo on
  // Options: 'chest_left' | 'chest_right' | 'back_center'
  logoZone: 'chest_left',

  // Fine-tune offsets WITHIN the zone (user-controlled sliders)
  decalTransform: {
    offsetX: 0.0,   // nudge left/right  (-1.0 to +1.0)
    offsetY: 0.0,   // nudge up/down     (-1.0 to +1.0)
    scale:   1.0,   // logo size         (0.2 to 2.0)
    rotate:  0.0,   // logo rotation     (-180 to +180 degrees)
  },

  // Canvas capture (for PDF)
  canvasSnapshot: null,

  // ── Setters ──────────────────────────────────────────────────
  setProductUrl:    (url)  => set({ productUrl: url }),
  setProductData:   (data) => set({ productData: data }),
  setColor:         (hex)  => set({ selectedColor: hex }),
  setLogoTexture:   (url)  => set({ logoTexture: url }),
  setLogoZone:      (zone) => set({ logoZone: zone }),
  setDecalTransform:(t)    => set({ decalTransform: t }),
  setCanvasSnapshot:(s)    => set({ canvasSnapshot: s }),
}))
```

---

## 🔑 Step 2 — Detect the Body Mesh in the GLB

The Sketchfab GLB has multiple meshes (body, zipper, buttons, etc.).
We need to find the largest/main fabric mesh to stamp the logo onto.
This utility does that automatically.

### `frontend/src/utils/findMeshByMaterial.js`

```js
import * as THREE from 'three'

/**
 * Walk the GLB scene graph and return the best candidate mesh
 * for logo decal placement.
 *
 * Strategy:
 *  1. If any mesh is named 'Body' or contains 'body'/'torso'/'shirt' → use it
 *  2. Otherwise use the mesh with the largest bounding box volume
 *     (almost always the main fabric body)
 */
export function findBodyMesh(scene) {
  const candidates = []

  scene.traverse((obj) => {
    if (!obj.isMesh) return
    if (!obj.geometry) return

    const name = (obj.name || '').toLowerCase()

    // Priority names from Sketchfab models
    const highPriority = ['body', 'torso', 'shirt', 'fabric',
                          'sweatshirt', 'hoodie', 'garment', 'cloth']

    if (highPriority.some(n => name.includes(n))) {
      candidates.unshift(obj)   // put at front
      return
    }

    candidates.push(obj)
  })

  if (candidates.length === 0) return null
  if (candidates.length === 1) return candidates[0]

  // If first candidate came from a priority name hit, use it
  const firstName = (candidates[0].name || '').toLowerCase()
  const highPriority = ['body', 'torso', 'shirt', 'fabric', 'sweatshirt']
  if (highPriority.some(n => firstName.includes(n))) return candidates[0]

  // Otherwise find the mesh with the largest bounding box
  let bestMesh = candidates[0]
  let bestVol  = 0

  for (const mesh of candidates) {
    const box = new THREE.Box3().setFromObject(mesh)
    const size = box.getSize(new THREE.Vector3())
    const vol  = size.x * size.y * size.z
    if (vol > bestVol) {
      bestVol  = vol
      bestMesh = mesh
    }
  }

  return bestMesh
}

/**
 * Given a logoZone string, return a {position, orientation, size} object
 * for DecalGeometry.
 *
 * These are RELATIVE values — they will be RAYCASTED onto the actual mesh
 * surface so they always land correctly regardless of GLB scale.
 *
 * Coordinate system: Three.js Y-up, model centered at origin
 */
export function getZoneConfig(zone) {
  const configs = {
    chest_left: {
      // Cast a ray from in front of the model, slightly left and up
      rayOrigin:    new THREE.Vector3(-0.15, 0.15, 2.0),
      rayDirection: new THREE.Vector3(0, 0, -1).normalize(),
      // If raycast misses, use this fallback world position
      fallback:     new THREE.Vector3(-0.15, 0.15, 0.28),
      decalSize:    new THREE.Vector3(0.20, 0.20, 0.20),
      label:        'Left Chest',
    },
    chest_right: {
      rayOrigin:    new THREE.Vector3(0.15, 0.15, 2.0),
      rayDirection: new THREE.Vector3(0, 0, -1).normalize(),
      fallback:     new THREE.Vector3(0.15, 0.15, 0.28),
      decalSize:    new THREE.Vector3(0.20, 0.20, 0.20),
      label:        'Right Chest',
    },
    back_center: {
      rayOrigin:    new THREE.Vector3(0, 0.05, -2.0),
      rayDirection: new THREE.Vector3(0, 0, 1).normalize(),
      fallback:     new THREE.Vector3(0, 0.05, -0.28),
      decalSize:    new THREE.Vector3(0.35, 0.35, 0.35),
      label:        'Back Center',
    },
  }
  return configs[zone] ?? configs['chest_left']
}
```

---

## 🔑 Step 3 — The Logo Hook (Core Logic)

This hook does all the heavy lifting. It is called from Viewer3D
and manages creating/removing/updating the decal mesh.

### `frontend/src/hooks/useDecalLogo.js`

```js
import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { DecalGeometry } from 'three/examples/jsm/geometries/DecalGeometry.js'
import { findBodyMesh, getZoneConfig } from '../utils/findMeshByMaterial'

/**
 * useDecalLogo
 *
 * Manages a THREE.js decal mesh that projects a logo onto the sweatshirt.
 *
 * @param {THREE.Scene}  scene           — the loaded GLB scene
 * @param {string|null}  logoUrl         — URL of the uploaded logo image
 * @param {string}       zone            — 'chest_left' | 'chest_right' | 'back_center'
 * @param {object}       transform       — { offsetX, offsetY, scale, rotate }
 */
export function useDecalLogo(scene, logoUrl, zone, transform) {
  const decalMeshRef  = useRef(null)
  const textureRef    = useRef(null)

  useEffect(() => {
    // ── Cleanup previous decal ────────────────────────────────────────────────
    if (decalMeshRef.current) {
      scene?.remove(decalMeshRef.current)
      decalMeshRef.current.geometry.dispose()
      decalMeshRef.current.material.dispose()
      decalMeshRef.current = null
    }

    if (!scene || !logoUrl) return

    // ── Find the body mesh ────────────────────────────────────────────────────
    const bodyMesh = findBodyMesh(scene)
    if (!bodyMesh) {
      console.warn('[DecalLogo] Could not find a body mesh in the GLB scene.')
      return
    }

    // ── Get zone config ───────────────────────────────────────────────────────
    const zoneConfig = getZoneConfig(zone)

    // ── Raycast to find exact surface position ────────────────────────────────
    // This ensures the decal always lands ON the surface, not floating in air
    const raycaster = new THREE.Raycaster(
      zoneConfig.rayOrigin,
      zoneConfig.rayDirection
    )
    const hits = raycaster.intersectObject(bodyMesh, false)

    let decalPosition, decalNormal

    if (hits.length > 0) {
      decalPosition = hits[0].point.clone()
      decalNormal   = hits[0].face.normal.clone()
        .transformDirection(bodyMesh.matrixWorld)
    } else {
      // Fallback: use the hardcoded position and point outward from center
      console.warn('[DecalLogo] Raycast missed — using fallback position for zone:', zone)
      decalPosition = zoneConfig.fallback.clone()
      decalNormal   = new THREE.Vector3(0, 0, 1)
    }

    // ── Apply user offsets (the sliders in the UI) ────────────────────────────
    // We move the position ALONG the surface, not through space,
    // by using the normal to define a local coordinate system
    const up      = new THREE.Vector3(0, 1, 0)
    const right   = new THREE.Vector3().crossVectors(decalNormal, up).normalize()
    const trueUp  = new THREE.Vector3().crossVectors(right, decalNormal).normalize()

    decalPosition.addScaledVector(right,   transform.offsetX * 0.08)
    decalPosition.addScaledVector(trueUp,  transform.offsetY * 0.08)

    // ── Build orientation (Euler) from the surface normal ─────────────────────
    const orientation = new THREE.Euler()
    const quaternion  = new THREE.Quaternion()
    quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), decalNormal)
    orientation.setFromQuaternion(quaternion)
    // Apply user rotation around the normal axis
    orientation.z += THREE.MathUtils.degToRad(transform.rotate)

    // ── Scale the decal ───────────────────────────────────────────────────────
    const baseSize = zoneConfig.decalSize.clone()
    const decalSize = baseSize.multiplyScalar(transform.scale)

    // ── Create DecalGeometry ──────────────────────────────────────────────────
    let geometry
    try {
      geometry = new DecalGeometry(bodyMesh, decalPosition, orientation, decalSize)
    } catch (err) {
      console.error('[DecalLogo] DecalGeometry failed:', err)
      return
    }

    // ── Load the logo texture ─────────────────────────────────────────────────
    const loader = new THREE.TextureLoader()
    loader.load(
      logoUrl,
      (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace
        textureRef.current = texture

        // ── Build decal material ──────────────────────────────────────────────
        // transparent: true so the PNG alpha channel works
        // depthWrite: false prevents z-fighting with the body mesh
        // polygonOffset pushes the decal slightly in front of the surface
        const material = new THREE.MeshStandardMaterial({
          map:           texture,
          transparent:   true,
          alphaTest:     0.01,
          depthWrite:    false,
          polygonOffset: true,
          polygonOffsetFactor: -4,
          polygonOffsetUnits:  -4,
          roughness:     0.85,    // makes it look printed/embroidered on fabric
          metalness:     0.0,
          side:          THREE.FrontSide,
        })

        // ── Add to scene ──────────────────────────────────────────────────────
        const decalMesh = new THREE.Mesh(geometry, material)
        decalMesh.name  = 'LogoDecal'
        decalMesh.renderOrder = 1   // render after the body mesh

        scene.add(decalMesh)
        decalMeshRef.current = decalMesh
      },
      undefined,
      (err) => console.error('[DecalLogo] Texture load failed:', err)
    )

    // ── Cleanup on next render ────────────────────────────────────────────────
    return () => {
      if (decalMeshRef.current) {
        scene.remove(decalMeshRef.current)
        decalMeshRef.current.geometry.dispose()
        decalMeshRef.current.material.dispose()
        decalMeshRef.current = null
      }
      if (textureRef.current) {
        textureRef.current.dispose()
        textureRef.current = null
      }
    }

  }, [scene, logoUrl, zone, transform])   // re-runs whenever ANY of these change
}
```

---

## 🔑 Step 4 — Rewrite Viewer3D.jsx

### `frontend/src/components/Viewer3D.jsx`

```jsx
import { Suspense, useRef, useCallback, useEffect } from 'react'
import { Canvas, useThree } from '@react-three/fiber'
import { OrbitControls, useGLTF, Environment, ContactShadows, Html } from '@react-three/drei'
import * as THREE from 'three'
import { useConfigurator } from '../store/configuratorStore'
import { useDecalLogo } from '../hooks/useDecalLogo'
import { findBodyMesh } from '../utils/findMeshByMaterial'

// ─── The actual 3D model ─────────────────────────────────────────────────────
function SweatshirtModel() {
  const { scene } = useGLTF('/models/quarter_zip.glb')

  const {
    selectedColor,
    logoTexture,
    logoZone,
    decalTransform,
  } = useConfigurator()

  // ── Color update ────────────────────────────────────────────────────────────
  // Walk every mesh in the GLB and tint fabric meshes with selectedColor.
  // We skip the zipper/buttons/hardware by checking roughness — fabric is rough.
  useEffect(() => {
    const color = new THREE.Color(selectedColor)
    scene.traverse((obj) => {
      if (!obj.isMesh || !obj.material) return
      if (obj.name === 'LogoDecal') return       // never tint the logo
      const mat = obj.material
      // Only tint materials that look like fabric (high roughness, low metalness)
      const roughness = mat.roughness ?? 1
      const metalness = mat.metalness ?? 0
      if (roughness > 0.5 && metalness < 0.3) {
        // Clone the material so we don't mutate the original
        if (!obj._originalMat) obj._originalMat = mat.clone()
        const newMat = obj._originalMat.clone()
        newMat.color = color
        obj.material = newMat
      }
    })
  }, [selectedColor, scene])

  // ── Logo decal ──────────────────────────────────────────────────────────────
  // The useDecalLogo hook manages the DecalGeometry lifecycle
  useDecalLogo(scene, logoTexture, logoZone, decalTransform)

  return (
    <primitive
      object={scene}
      scale={1.4}
      position={[0, -1.0, 0]}
      castShadow
      receiveShadow
    />
  )
}

// ─── Loading spinner ─────────────────────────────────────────────────────────
function Loader() {
  return (
    <Html center>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div className="w-10 h-10 border-4 border-ipromo-teal border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-ipromo-navy font-medium">Loading 3D model…</span>
      </div>
    </Html>
  )
}

// ─── Canvas capture helper (used by PDF button) ───────────────────────────────
function CaptureHelper({ onRegisterCapture }) {
  const { gl } = useThree()
  useEffect(() => {
    onRegisterCapture(() => gl.domElement.toDataURL('image/png'))
  }, [gl, onRegisterCapture])
  return null
}

// ─── Main exported component ─────────────────────────────────────────────────
export default function Viewer3D({ onRegisterCapture }) {
  return (
    <div className="w-full h-full rounded-2xl overflow-hidden bg-gradient-to-b from-slate-100 to-slate-200 relative">
      <Canvas
        camera={{ position: [0, 0.5, 3.2], fov: 45 }}
        shadows
        gl={{ preserveDrawingBuffer: true }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 10, 5]}  intensity={1.2} castShadow shadow-mapSize={[2048, 2048]} />
        <directionalLight position={[-4, 5, -3]} intensity={0.4} color="#cce0ff" />
        <pointLight        position={[0, 3, 2]}  intensity={0.3} color="#fff8f0" />

        {/* HDRI for reflections */}
        <Environment preset="studio" />

        {/* Model */}
        <Suspense fallback={<Loader />}>
          <SweatshirtModel />
        </Suspense>

        {/* Ground shadow */}
        <ContactShadows position={[0, -1.8, 0]} opacity={0.5} scale={6} blur={2.5} far={4} />

        {/* Camera controls */}
        <OrbitControls
          enablePan={false}
          minPolarAngle={Math.PI / 6}
          maxPolarAngle={Math.PI * 0.8}
          minDistance={1.8}
          maxDistance={5}
          autoRotate
          autoRotateSpeed={0.6}
        />

        {/* Register canvas capture for PDF */}
        {onRegisterCapture && <CaptureHelper onRegisterCapture={onRegisterCapture} />}
      </Canvas>

      {/* Overlay label */}
      <div className="absolute bottom-3 left-3 text-xs text-slate-400 pointer-events-none">
        Drag to rotate · Scroll to zoom
      </div>
    </div>
  )
}
```

---

## 🔑 Step 5 — Rewrite LogoUploader.jsx (Zone Selector + Sliders)

### `frontend/src/components/LogoUploader.jsx`

```jsx
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { Upload, X, RotateCcw } from 'lucide-react'

// Zone options shown to the user
const ZONES = [
  { id: 'chest_left',  label: 'Left Chest',   icon: '◧' },
  { id: 'chest_right', label: 'Right Chest',  icon: '◨' },
  { id: 'back_center', label: 'Back Center',  icon: '□' },
]

// Slider config: key into decalTransform, label, min, max, step, unit
const SLIDERS = [
  { key: 'offsetX', label: 'Move ←→',  min: -1,   max: 1,   step: 0.05, unit: '' },
  { key: 'offsetY', label: 'Move ↑↓',  min: -1,   max: 1,   step: 0.05, unit: '' },
  { key: 'scale',   label: 'Size',     min: 0.2,  max: 2.0, step: 0.05, unit: 'x' },
  { key: 'rotate',  label: 'Rotate',   min: -180, max: 180, step: 1,    unit: '°' },
]

const DEFAULT_TRANSFORM = { offsetX: 0, offsetY: 0, scale: 1.0, rotate: 0 }

export default function LogoUploader() {
  const {
    logoTexture, setLogoTexture,
    logoZone,    setLogoZone,
    decalTransform, setDecalTransform,
  } = useConfigurator()

  const [preview,   setPreview]   = useState(null)
  const [uploading, setUploading] = useState(false)

  // ── File drop handler ────────────────────────────────────────────────────────
  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return

    const previewUrl = URL.createObjectURL(file)
    setPreview(previewUrl)
    setUploading(true)

    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post('/api/upload/logo', form)

      setLogoTexture(data.logo_url)
      toast.success('Logo applied! Rotate the model to see it.')
    } catch {
      toast.error('Upload failed — please try again')
    } finally {
      setUploading(false)
    }
  }, [setLogoTexture])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/png': [], 'image/jpeg': [], 'image/svg+xml': [] },
    maxFiles: 1,
    maxSize: 5_000_000,
  })

  // ── Remove logo ──────────────────────────────────────────────────────────────
  const removeLogo = (e) => {
    e.stopPropagation()
    setPreview(null)
    setLogoTexture(null)
    setDecalTransform(DEFAULT_TRANSFORM)
  }

  // ── Reset sliders ────────────────────────────────────────────────────────────
  const resetTransform = () => setDecalTransform(DEFAULT_TRANSFORM)

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-4">
      <h3 className="text-sm font-semibold text-ipromo-navy">2. Upload Your Logo</h3>

      {/* ── Drop zone ─────────────────────────────────────────────────────────── */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors
          ${isDragActive
            ? 'border-ipromo-teal bg-teal-50'
            : 'border-slate-200 hover:border-ipromo-teal hover:bg-slate-50'}
        `}
      >
        <input {...getInputProps()} />
        {preview ? (
          <div className="flex items-center justify-between">
            <img src={preview} alt="logo preview" className="h-12 object-contain rounded" />
            <div className="flex items-center gap-2">
              <span className="text-xs text-green-600 font-medium">✓ Applied</span>
              <button onClick={removeLogo} className="text-slate-400 hover:text-red-400 p-1">
                <X size={14} />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-2">
            <Upload size={28} className="text-ipromo-teal" />
            <p className="text-xs text-slate-500">
              {uploading
                ? '⏳ Uploading…'
                : 'Drop your PNG / JPG / SVG here, or click to browse'}
            </p>
            <p className="text-xs text-slate-400">Max 5 MB · Transparent PNG recommended</p>
          </div>
        )}
      </div>

      {/* ── Zone selector (only shown after logo upload) ───────────────────── */}
      {logoTexture && (
        <div className="space-y-3">
          {/* Zone buttons */}
          <div>
            <p className="text-xs font-medium text-slate-600 mb-2">Logo position</p>
            <div className="flex gap-2">
              {ZONES.map(({ id, label, icon }) => (
                <button
                  key={id}
                  onClick={() => setLogoZone(id)}
                  className={`
                    flex-1 py-2 px-2 rounded-lg border text-xs font-medium transition-all
                    ${logoZone === id
                      ? 'border-ipromo-teal bg-teal-50 text-ipromo-teal'
                      : 'border-slate-200 text-slate-500 hover:border-ipromo-teal'}
                  `}
                >
                  <span className="block text-base mb-0.5">{icon}</span>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Fine-tune sliders */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium text-slate-600">Fine-tune</p>
              <button
                onClick={resetTransform}
                className="text-xs text-slate-400 hover:text-ipromo-teal flex items-center gap-1"
              >
                <RotateCcw size={11} /> Reset
              </button>
            </div>
            <div className="space-y-2">
              {SLIDERS.map(({ key, label, min, max, step, unit }) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 w-16 flex-shrink-0">{label}</span>
                  <input
                    type="range"
                    min={min} max={max} step={step}
                    value={decalTransform[key]}
                    onChange={(e) =>
                      setDecalTransform({
                        ...decalTransform,
                        [key]: parseFloat(e.target.value)
                      })
                    }
                    className="flex-1 accent-ipromo-teal h-1"
                  />
                  <span className="text-xs text-slate-400 w-10 text-right">
                    {decalTransform[key]}{unit}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Tip box */}
          <div className="bg-blue-50 rounded-lg px-3 py-2">
            <p className="text-xs text-blue-700">
              💡 <strong>Tip:</strong> Rotate the model to see the logo from all angles.
              Use the sliders to adjust position and size. Transparent PNG logos look best.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## 🔑 Step 6 — Verify DecalGeometry Import Path

Different Three.js versions have the import at slightly different paths.
Here is a safe import that works across versions:

```js
// Try this first (Three.js >= 0.150):
import { DecalGeometry } from 'three/examples/jsm/geometries/DecalGeometry.js'

// If that gives a "module not found" error, try:
import { DecalGeometry } from 'three-stdlib'

// Then install: npm install three-stdlib
```

Add this test to your browser console after loading the page to confirm it works:
```js
import('three/examples/jsm/geometries/DecalGeometry.js')
  .then(m => console.log('✅ DecalGeometry available', m))
  .catch(e => console.error('❌ Import failed', e))
```

---

## 🐛 Troubleshooting: Logo Still Not Showing?

Work through this checklist in order:

### Check 1 — Is the texture loading?

Open browser DevTools → Network tab → filter by your domain/localhost.
After uploading a logo, you should see a request to `/static/uploads/xxx.png`
returning **200 OK**. If you see 404 → the backend is not serving static files.

Fix in `main.py`:
```python
# Make sure this line exists in main.py BEFORE your router includes:
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Check 2 — Is findBodyMesh finding anything?

Add this debug line inside SweatshirtModel in Viewer3D.jsx:
```js
useEffect(() => {
  if (!scene) return
  console.log('[DEBUG] All meshes in GLB:')
  scene.traverse(obj => {
    if (obj.isMesh) console.log('  mesh:', obj.name, '| material:', obj.material?.name)
  })
}, [scene])
```
Look at the console. You'll see the actual mesh names from your Sketchfab GLB.
Then update the `highPriority` array in `findMeshByMaterial.js` to match those names.

### Check 3 — Is the raycast hitting the mesh?

Add this debug inside `useDecalLogo.js` after the raycast:
```js
console.log('[DEBUG] Raycast hits:', hits.length, hits[0]?.point)
```
If `hits.length === 0`, the raycast is missing. This can happen if:
- The model is much larger or smaller than expected (GLB scale varies a lot)
- The model is not centered at origin

Fix: Scale your rayOrigin values by the actual bounding box of the model.
Add this right after `const bodyMesh = findBodyMesh(scene)`:
```js
const bbox = new THREE.Box3().setFromObject(bodyMesh)
const center = bbox.getCenter(new THREE.Vector3())
const size   = bbox.getSize(new THREE.Vector3())
console.log('[DEBUG] Model center:', center, '| size:', size)

// Adjust ray to shoot from in front of the model's actual center
zoneConfig.rayOrigin.set(
  center.x + (zone === 'chest_left' ? -size.x * 0.15 : zone === 'chest_right' ? size.x * 0.15 : 0),
  center.y + size.y * 0.10,
  center.z + size.z * 3.0   // far in front
)
zoneConfig.fallback.copy(center).setZ(center.z + size.z * 0.45)
```

### Check 4 — Is the decal z-fighting (flickering)?

Symptom: logo flickers or disappears when rotating.
Fix: Increase the polygonOffset values in the material:
```js
polygonOffsetFactor: -8,   // was -4
polygonOffsetUnits:  -8,   // was -4
```

### Check 5 — Is the logo PNG transparent?

SVG and PNG with white backgrounds will show a white box around the logo.
Tell users to upload PNG with transparent background.
You can auto-strip white backgrounds server-side using Pillow:

```python
# In backend/routers/upload.py, after saving the file:
from PIL import Image
import io

if file.content_type in ("image/jpeg", "image/png"):
    img = Image.open(path).convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        # Make near-white pixels transparent
        if item[0] > 220 and item[1] > 220 and item[2] > 220:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)
    img.save(path, "PNG")
```

---

## 📋 Summary: Build Order for IDE Agent

```
Phase 1 — Fix logo placement (do this first)
─────────────────────────────────────────────
Step 1.  Create frontend/src/utils/findMeshByMaterial.js  (copy from above)
Step 2.  Create frontend/src/hooks/useDecalLogo.js         (copy from above)
Step 3.  Update frontend/src/store/configuratorStore.js    (add logoZone + decalTransform)
Step 4.  Rewrite frontend/src/components/Viewer3D.jsx      (use useDecalLogo hook)
Step 5.  Rewrite frontend/src/components/LogoUploader.jsx  (add zones + sliders)
Step 6.  Run dev server, upload a PNG, check browser console for [DEBUG] messages
Step 7.  Fix any raycast miss issues using Check 3 debug steps above

Phase 2 — Color, Share, PDF (after logo works)
──────────────────────────────────────────────
Step 8.  Test color picker — verify fabric meshes change color, zipper does not
Step 9.  Wire ShareButton → POST /api/configs/ → get UUID → build share URL
Step 10. Wire PDFDownloadButton → capture canvas → POST /api/pdf/download
Step 11. Test SharedViewPage at /share/:uuid — loads correct color + logo
Step 12. Final QA: rotate, zoom, change color, change logo zone, download PDF
```

---

## 🏁 Quick Glossary (for reference)

| Term | What it means in plain English |
|---|---|
| GLB | The 3D model file. You download it once from Sketchfab, never modify it. |
| Material | The "paint" on a 3D mesh. We change its color property live in JS. |
| Mesh | A single 3D shape inside the GLB (e.g. the body, the zipper). |
| DecalGeometry | Three.js tool that "stamps" an image onto a mesh surface, hugging its curves. |
| Raycast | Shooting an invisible ray from a point in 3D space to find where it hits a mesh. Used to find the exact surface point for the decal. |
| UV | A 2D coordinate system that maps a flat image onto a 3D surface. DecalGeometry handles this automatically — you don't touch UVs. |
| polygonOffset | A GPU trick to prevent z-fighting (flickering) when two surfaces occupy the same space. |