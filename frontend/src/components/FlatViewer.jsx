import { useEffect, useRef, useState } from 'react'
import { useConfigurator } from '../store/configuratorStore'

export default function FlatViewer({ images, onRegisterCapture }) {
  const canvasRef = useRef(null)
  const [currentImage, setCurrentImage] = useState(0)
  const { selectedColor, logoTexture, decalTransform } = useConfigurator()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !images?.length) return
    const ctx = canvas.getContext('2d')

    const productImg = new Image()
    productImg.crossOrigin = 'anonymous'
    productImg.src = images[currentImage]

    productImg.onload = () => {
      canvas.width  = productImg.naturalWidth  || 600
      canvas.height = productImg.naturalHeight || 600
      ctx.drawImage(productImg, 0, 0)

      ctx.globalAlpha = 0.25
      ctx.fillStyle = selectedColor
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.globalAlpha = 1.0

      if (!logoTexture) return
      const logoImg = new Image()
      logoImg.crossOrigin = 'anonymous'
      logoImg.src = logoTexture

      logoImg.onload = () => {
        const scale = decalTransform.scale ?? 1.0
        const w = canvas.width  * 0.22 * scale
        const h = canvas.height * 0.22 * scale
        const x = canvas.width  * 0.25 + (decalTransform.offsetX ?? 0) * 50
        const y = canvas.height * 0.35 + (decalTransform.offsetY ?? 0) * 50

        ctx.save()
        ctx.translate(x + w / 2, y + h / 2)
        ctx.rotate((decalTransform.rotate ?? 0) * Math.PI / 180)
        ctx.drawImage(logoImg, -w / 2, -h / 2, w, h)
        ctx.restore()
      }
    }
  }, [images, currentImage, selectedColor, logoTexture, decalTransform])

  useEffect(() => {
    onRegisterCapture?.(() => canvasRef.current?.toDataURL('image/png'))
  }, [onRegisterCapture])

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden bg-slate-100 flex flex-col relative">
      <canvas
        ref={canvasRef}
        className="flex-1 w-full object-contain"
        style={{ imageRendering: 'auto' }}
      />

      {images?.length > 1 && (
        <div className="flex gap-2 p-3 justify-center bg-white">
          {images.slice(0, 5).map((src, i) => (
            <button
              key={i}
              onClick={() => setCurrentImage(i)}
              className={`w-12 h-12 rounded-lg overflow-hidden border-2 transition-all
                ${currentImage === i ? 'border-ipromo-teal' : 'border-transparent'}`}
            >
              <img src={src} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      <div className="absolute top-3 right-3 bg-amber-100 text-amber-800 text-xs
                      px-2 py-1 rounded-lg border border-amber-200">
        📸 Photo preview — 3D model coming soon for this category
      </div>
    </div>
  )
}
