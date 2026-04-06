import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import client from '../api/client'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { Upload, X, RotateCcw } from 'lucide-react'

const ZONES = [
  { id: 'chest_left',  label: 'Left Chest',  icon: '◧' },
  { id: 'chest_right', label: 'Right Chest', icon: '◨' },
  { id: 'back_center', label: 'Back Center', icon: '□' },
]

const SLIDERS = [
  { key: 'offsetX', label: 'Move ←→', min: -1,   max: 1,   step: 0.05, unit: '' },
  { key: 'offsetY', label: 'Move ↑↓', min: -1,   max: 1,   step: 0.05, unit: '' },
  { key: 'scale',   label: 'Size',    min: 0.2,  max: 2.0, step: 0.05, unit: 'x' },
  { key: 'rotate',  label: 'Rotate',  min: -180, max: 180, step: 1,    unit: '°' },
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

  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await client.post('/api/upload/logo', form)
      setLogoTexture(data.logo_url)
      toast.success('Logo applied! Rotate the model to see it.')
    } catch {
      toast.error('Upload failed — try again')
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

  const removeLogo = (e) => {
    e.stopPropagation()
    setPreview(null)
    setLogoTexture(null)
    setDecalTransform(DEFAULT_TRANSFORM)
  }

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-4">
      <h3 className="text-sm font-semibold text-ipromo-navy">2. Upload Your Logo</h3>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-ipromo-teal bg-teal-50' : 'border-slate-200 hover:border-ipromo-teal hover:bg-slate-50'}`}
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
              {uploading ? '⏳ Uploading…' : 'Drop PNG / JPG / SVG here, or click to browse'}
            </p>
            <p className="text-xs text-slate-400">Max 5 MB · Transparent PNG recommended</p>
          </div>
        )}
      </div>

      {logoTexture && (
        <div className="space-y-3">
          {/* Zone selector */}
          <div>
            <p className="text-xs font-medium text-slate-600 mb-2">Logo position</p>
            <div className="flex gap-2">
              {ZONES.map(({ id, label, icon }) => (
                <button
                  key={id}
                  onClick={() => setLogoZone(id)}
                  className={`flex-1 py-2 px-2 rounded-lg border text-xs font-medium transition-all
                    ${logoZone === id
                      ? 'border-ipromo-teal bg-teal-50 text-ipromo-teal'
                      : 'border-slate-200 text-slate-500 hover:border-ipromo-teal'}`}
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
                onClick={() => setDecalTransform(DEFAULT_TRANSFORM)}
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
                    onChange={(e) => setDecalTransform({ ...decalTransform, [key]: parseFloat(e.target.value) })}
                    className="flex-1 accent-ipromo-teal h-1"
                  />
                  <span className="text-xs text-slate-400 w-10 text-right">
                    {decalTransform[key]}{unit}
                  </span>
                </div>
              ))}
            </div>
          </div>

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
