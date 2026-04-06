import { Suspense, useRef, useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF, Environment, ContactShadows, Html } from '@react-three/drei'
import * as THREE from 'three'
import { useConfigurator } from '../store/configuratorStore'

function SweatshirtModel() {
  const { scene } = useGLTF('/models/quarter_zip.glb')
  const { selectedColor, logoTexture } = useConfigurator()

  useEffect(() => {
    scene.traverse((child) => {
      if (child.isMesh && child.material?.name === 'Body') {
        child.material = child.material.clone()
        child.material.color.set(selectedColor)
        child.material.needsUpdate = true
      }
    })
  }, [selectedColor, scene])

  useEffect(() => {
    if (!logoTexture) return
    scene.traverse((child) => {
      if (child.isMesh && child.name === 'LogoPlane_Chest') {
        const tex = new THREE.TextureLoader().load(logoTexture)
        tex.colorSpace = THREE.SRGBColorSpace
        child.material = new THREE.MeshStandardMaterial({
          map: tex,
          transparent: true,
          alphaTest: 0.05,
          depthWrite: false,
          roughness: 0.8,
          metalness: 0.0,
        })
      }
    })
  }, [logoTexture, scene])

  return (
    <primitive object={scene} scale={1.4} position={[0, -1.0, 0]} castShadow receiveShadow />
  )
}

function Loader() {
  return (
    <Html center>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, minWidth: 160 }}>
        <div style={{
          width: 48, height: 48, border: '4px solid #00B5B8',
          borderTopColor: 'transparent', borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }} />
        <span style={{ fontSize: 13, color: '#1B2A6B', fontWeight: 600, letterSpacing: 0.2 }}>Loading 3D model…</span>
        <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
          {[0,1,2].map(i => (
            <div key={i} style={{
              width: 8, height: 8, borderRadius: '50%', background: '#00B5B8',
              animation: `bounce 1s ease-in-out ${i * 0.2}s infinite alternate`
            }} />
          ))}
        </div>
        <style>{`
          @keyframes spin { to { transform: rotate(360deg) } }
          @keyframes bounce { from { transform: translateY(0) } to { transform: translateY(-6px) } }
        `}</style>
      </div>
    </Html>
  )
}

export default function Viewer3D({ canvasRef, onCapture }) {
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
        <directionalLight position={[5, 10, 5]} intensity={1.2} castShadow shadow-mapSize={[2048, 2048]} />
        <directionalLight position={[-4, 5, -3]} intensity={0.4} color="#cce0ff" />
        <pointLight position={[0, 3, 2]} intensity={0.3} color="#fff8f0" />

        <Environment preset="studio" />

        <Suspense fallback={<Loader />}>
          <SweatshirtModel />
        </Suspense>

        <ContactShadows position={[0, -1.8, 0]} opacity={0.5} scale={6} blur={2.5} far={4} />

        {/* Step 30: stop autoRotate when user grabs the model */}
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
      </Canvas>

      {/* Rotate hint — fades once user interacts */}
      {autoRotate && (
        <div className="absolute bottom-14 left-1/2 -translate-x-1/2 text-xs text-slate-400 pointer-events-none select-none">
          🖱 Drag to rotate
        </div>
      )}

      <button
        className="absolute bottom-4 right-4 bg-ipromo-navy text-white px-3 py-1.5 rounded-lg text-xs opacity-70 hover:opacity-100 transition-opacity"
        onClick={() => {
          if (rendererRef.current) {
            const dataUrl = rendererRef.current.domElement.toDataURL('image/png')
            onCapture?.(dataUrl)
          }
        }}
      >
        📸 Capture
      </button>
    </div>
  )
}
