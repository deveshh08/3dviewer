import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { Upload, X, Move } from 'lucide-react'

export default function LogoUploader() {
  const { setLogoTexture, logoTransform, setLogoTransform } = useConfigurator()
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post('/api/upload/logo', form)
      setLogoTexture(data.logo_url)
      toast.success('Logo applied to model!')
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

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-4">
      <h3 className="text-sm font-semibold text-ipromo-navy">2. Upload Your Logo</h3>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors duration-200
          ${isDragActive ? 'border-ipromo-teal bg-teal-50' : 'border-slate-200 hover:border-ipromo-teal'}`}
      >
        <input {...getInputProps()} />
        {preview ? (
          <div className="flex items-center justify-center gap-3">
            <img src={preview} alt="logo" className="h-12 object-contain rounded" />
            <button
              className="text-slate-400 hover:text-red-400"
              onClick={(e) => { e.stopPropagation(); setPreview(null); setLogoTexture(null) }}
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <>
            <Upload className="mx-auto mb-2 text-ipromo-teal" size={28} />
            <p className="text-xs text-slate-500">
              {uploading ? 'Uploading…' : 'Drag & drop PNG / JPG / SVG or click to browse'}
            </p>
          </>
        )}
      </div>

      {preview && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
            <Move size={12} /> Position & Size
          </label>
          {[
            { key: 'x', label: 'Left ↔ Right', min: -0.5, max: 0.5 },
            { key: 'y', label: 'Up ↕ Down',    min: -0.5, max: 0.5 },
            { key: 's', label: 'Scale',         min: 0.05, max: 0.5 },
          ].map(({ key, label, min, max }) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-xs text-slate-400 w-20">{label}</span>
              <input
                type="range" min={min} max={max} step={0.01}
                value={logoTransform[key] ?? (key === 's' ? 0.18 : 0)}
                onChange={(e) => setLogoTransform({ ...logoTransform, [key]: parseFloat(e.target.value) })}
                className="flex-1 accent-ipromo-teal"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
