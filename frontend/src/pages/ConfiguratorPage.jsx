import { useRef, useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Viewer3D from '../components/Viewer3D'
import ColorPicker from '../components/ColorPicker'
import LogoUploader from '../components/LogoUploader'
import ShareButton from '../components/ShareButton'
import PDFDownloadButton from '../components/PDFDownloadButton'
import ProductInfo from '../components/ProductInfo'
import { useConfigurator } from '../store/configuratorStore'
import axios from 'axios'
import toast, { Toaster } from 'react-hot-toast'

export default function ConfiguratorPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const productUrl = searchParams.get('url') ?? 'https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html'
  const { setProductData, setProductUrl } = useConfigurator()
  const canvasRef = useRef(null)
  const [urlInput, setUrlInput] = useState(productUrl)

  useEffect(() => {
    setProductUrl(productUrl)
    setUrlInput(productUrl)
    axios.get(`/api/products/?url=${encodeURIComponent(productUrl)}`)
      .then(({ data }) => setProductData(data))
      .catch(() => toast.error('Could not load product data'))
  }, [productUrl])

  const handleUrlSubmit = (e) => {
    e.preventDefault()
    const trimmed = urlInput.trim()
    if (!trimmed) return
    navigate(`/?url=${encodeURIComponent(trimmed)}`)
  }

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <Navbar />
      <Toaster position="top-right" />

      {/* Step 32: URL input bar */}
      <div className="bg-white border-b border-slate-200 px-4 py-2">
        <form onSubmit={handleUrlSubmit} className="max-w-7xl mx-auto flex gap-2">
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="Paste any iPromo product URL…"
            className="flex-1 text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-ipromo-teal"
          />
          <button
            type="submit"
            className="bg-ipromo-teal text-white text-xs px-4 py-2 rounded-lg hover:bg-teal-600 transition-colors whitespace-nowrap"
          >
            Load Product
          </button>
        </form>
      </div>

      {/* Step 28: grid-cols-1 on mobile stacks viewer above controls */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
        {/* 3D Viewer */}
        <div className="relative h-[420px] sm:h-[520px] lg:h-auto lg:min-h-[580px]">
          <Viewer3D canvasRef={canvasRef} onCapture={() => {}} />
        </div>

        {/* Control panel — scrollable on mobile */}
        <aside className="flex flex-col gap-4 overflow-y-auto lg:overflow-visible pb-4">
          <ProductInfo />
          <ColorPicker />
          <LogoUploader />

          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-sm font-semibold text-ipromo-navy">3. Share & Export</h3>
            <ShareButton />
            <PDFDownloadButton canvasRef={canvasRef} />
          </div>

          {/* Pricing table */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
            <h3 className="text-sm font-semibold text-ipromo-navy mb-3">Quantity Pricing</h3>
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-ipromo-navy text-white">
                  {['12–23','24–47','48–95','96–143','144+'].map(q =>
                    <th key={q} className="py-1.5 px-2 text-center">{q}</th>
                  )}
                </tr>
              </thead>
              <tbody>
                <tr className="bg-slate-50">
                  {['$51.99','$49.99','$47.99','$45.99','$43.99'].map(p =>
                    <td key={p} className="py-1.5 px-2 text-center font-medium">{p}</td>
                  )}
                </tr>
              </tbody>
            </table>
            <p className="text-xs text-slate-400 mt-2">Setup Charge: $75.00 · Min qty: 12</p>
          </div>
        </aside>
      </main>
    </div>
  )
}
