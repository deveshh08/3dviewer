import { Suspense, useRef, useEffect, useState } from 'react'
import { Canvas, useThree } from '@react-three/fiber'
import { OrbitControls, useGLTF, Environment, ContactShadows, Html } from '@react-three/drei'
import * as THREE from 'three'
import { useConfigurator } from '../store/configuratorStore'
import { useDecalLogo } from '../hooks/useDecalLogo'

function SweatshirtModel() {
  const { scene } = useGLTF('/models/quarter_zip.glb')
  const { selectedColor, logoTexture, logoZone, decalTransform } = useConfigurator()
  const modelRef = useRef()

  // Debug: log all mesh names once on load
  useEffect(() => {
    console.log('[Viewer3D] Meshes in GLB:')
    scene.traverse(obj => {
      if (obj.isMesh) console.log('  mesh:', obj.name, '| mat:', obj.material?.name, '| roughness:', obj.material?.roughness)
    })
  }, [scene])

  // Color: tint all meshes except known metal/hardware parts
  useEffect(() => {
    const color = new THREE.Color(selectedColor)
    const exclude = ['zipper', 'zip', 'button', 'snap', 'buckle', 'metal', 'hardware', 'toggle', 'cord', 'eyelet']
    scene.traverse((obj) => {
      if (!obj.isMesh || !obj.material) return
      if (obj.name === 'LogoDecal') return
      const name = (obj.name + ' ' + (obj.material.name ?? '')).toLowerCase()
      if (exclude.some(k => name.includes(k))) return
      if (!obj._originalMat) obj._originalMat = obj.material.clone()
      const newMat = obj._originalMat.clone()
      newMat.color = color
      obj.material = newMat
    })
  }, [selectedColor, scene])

  // Logo decal — pass modelRef so the hook can raycast against the mounted, world-transformed mesh
  useDecalLogo(modelRef, logoTexture, logoZone, decalTransform)

  return (
    <primitive
      ref={modelRef}
      object={scene}
      scale={1.4}
      position={[0, -1.0, 0]}
      castShadow
      receiveShadow
    />
  )
}

function Loader() {
  return (
    <Html center>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 48, height: 48, border: '4px solid #00B5B8',
          borderTopColor: 'transparent', borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }} />
        <span style={{ fontSize: 13, color: '#1B2A6B', fontWeight: 600 }}>Loading 3D model…</span>
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    </Html>
  )
}

function CaptureHelper({ onRegisterCapture }) {
  const { gl } = useThree()
  useEffect(() => {
    onRegisterCapture?.(() => gl.domElement.toDataURL('image/png'))
  }, [gl, onRegisterCapture])
  return null
}

export default function Viewer3D({ canvasRef, onCapture, onRegisterCapture }) {
  const rendererRef = useRef()
  const [autoRotate, setAutoRotate] = useState(true)

  return (
    <div className="w-full h-full min-h-[320px] rounded-2xl overflow-hidden bg-gradient-to-b from-slate-100 to-slate-200 relative">
      <Canvas
        camera={{ position: [0, 0.5, 3.2], fov: 45 }}
        shadows
        gl={{ preserveDrawingBuffer: true }}
        onCreated={({ gl }) => {
          rendererRef.current = gl
          if (canvasRef) canvasRef.current = gl.domElement
        }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 10, 5]}  intensity={1.2} castShadow shadow-mapSize={[2048, 2048]} />
        <directionalLight position={[-4, 5, -3]} intensity={0.4} color="#cce0ff" />
        <pointLight        position={[0, 3, 2]}  intensity={0.3} color="#fff8f0" />

        <Environment preset="studio" />

        <Suspense fallback={<Loader />}>
          <SweatshirtModel />
        </Suspense>

        <ContactShadows position={[0, -1.8, 0]} opacity={0.5} scale={6} blur={2.5} far={4} />

        <OrbitControls
          enablePan={false}
          minPolarAngle={Math.PI / 6}
          maxPolarAngle={Math.PI * 0.8}
          minDistance={1.8}
          maxDistance={5}
          autoRotate={autoRotate}
          autoRotateSpeed={0.6}
          onStart={() => setAutoRotate(false)}
        />

        {onRegisterCapture && <CaptureHelper onRegisterCapture={onRegisterCapture} />}
      </Canvas>

      {autoRotate && (
        <div className="absolute bottom-14 left-1/2 -translate-x-1/2 text-xs text-slate-400 pointer-events-none select-none">
          🖱 Drag to rotate
        </div>
      )}

      <button
        className="absolute bottom-4 right-4 bg-ipromo-navy text-white px-3 py-1.5 rounded-lg text-xs opacity-70 hover:opacity-100 transition-opacity"
        onClick={() => {
          const dataUrl = rendererRef.current?.domElement.toDataURL('image/png')
          onCapture?.(dataUrl)
        }}
      >
        📸 Capture
      </button>
    </div>
  )
}
