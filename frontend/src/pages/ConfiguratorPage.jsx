import { useEffect, useState, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import axios from 'axios'
import toast, { Toaster } from 'react-hot-toast'
import Navbar from '../components/Navbar'
import Viewer3D from '../components/Viewer3D'
import FlatViewer from '../components/FlatViewer'
import ColorPicker from '../components/ColorPicker'
import LogoUploader from '../components/LogoUploader'
import ShareButton from '../components/ShareButton'
import PDFDownloadButton from '../components/PDFDownloadButton'
import ProductInfo from '../components/ProductInfo'
import { useConfigurator } from '../store/configuratorStore'

export default function ConfiguratorPage() {
  const [searchParams] = useSearchParams()
  const productUrl = searchParams.get('url') ?? ''
  const [loading, setLoading] = useState(false)
  const captureRef = useRef(null)

  const { setProductData, setProductUrl, productData } = useConfigurator()

  useEffect(() => {
    if (!productUrl) return
    setProductUrl(productUrl)
    setLoading(true)

    axios.get(`/api/products/?url=${encodeURIComponent(productUrl)}`)
      .then(({ data }) => {
        setProductData(data)
        if (!data.glb_file) {
          toast('No 3D model for this category — showing photo preview', {
            icon: '📸',
            duration: 4000,
          })
        }
      })
      .catch(() => toast.error('Could not load product — check the URL'))
      .finally(() => setLoading(false))
  }, [productUrl])

  const onRegisterCapture = useCallback((fn) => {
    captureRef.current = fn
  }, [])

  if (!productUrl) {
    return <URLInputScreen />
  }

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <Navbar />
      <Toaster position="top-right" />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6
                       grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">

        <div className="relative h-[520px] lg:h-auto lg:min-h-[580px]">
          {loading && <ViewerSkeleton />}

          {!loading && productData && (
            productData.glb_file
              ? <Viewer3D
                  glbFile={`/models/${productData.glb_file}`}
                  onRegisterCapture={onRegisterCapture}
                />
              : <FlatViewer
                  images={productData.images}
                  onRegisterCapture={onRegisterCapture}
                />
          )}
        </div>

        <aside className="flex flex-col gap-4">
          <ProductInfo />
          <ColorPicker />
          <LogoUploader />
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-sm font-semibold text-ipromo-navy">3. Share & Export</h3>
            <ShareButton captureRef={captureRef} />
            <PDFDownloadButton captureRef={captureRef} />
          </div>

          {/* Pricing table */}
          {productData?.pricing_tiers && (
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <h3 className="text-sm font-semibold text-ipromo-navy mb-3">Quantity Pricing</h3>
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-ipromo-navy text-white">
                    {productData.pricing_tiers.map(t =>
                      <th key={t.qty} className="py-1.5 px-2 text-center">{t.qty}</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  <tr className="bg-slate-50">
                    {productData.pricing_tiers.map(t =>
                      <td key={t.qty} className="py-1.5 px-2 text-center font-medium">{t.price}</td>
                    )}
                  </tr>
                </tbody>
              </table>
              <p className="text-xs text-slate-400 mt-2">Setup Charge: $75.00 · Min qty: 12</p>
            </div>
          )}
        </aside>
      </main>
    </div>
  )
}

function URLInputScreen() {
  const [inputUrl, setInputUrl] = useState('')

  const go = () => {
    if (!inputUrl.includes('ipromo.com')) {
      toast.error('Please paste an iPromo product URL')
      return
    }
    window.location.href = `/?url=${encodeURIComponent(inputUrl)}`
  }

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <Navbar />
      <Toaster position="top-right" />
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="bg-white rounded-3xl p-8 shadow-lg max-w-lg w-full space-y-5">
          <div className="text-center">
            <img src="/ipromo_logo.png" alt="iPromo" className="h-10 mx-auto mb-3" />
            <h1 className="text-xl font-semibold text-ipromo-navy">3D Product Configurator</h1>
            <p className="text-sm text-slate-500 mt-1">
              Paste any iPromo product URL to see it in 3D with your logo
            </p>
          </div>

          <div className="space-y-2">
            <input
              type="url"
              value={inputUrl}
              onChange={e => setInputUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && go()}
              placeholder="https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html"
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm
                         focus:outline-none focus:ring-2 focus:ring-ipromo-teal"
            />
            <button
              onClick={go}
              className="w-full bg-ipromo-navy text-white py-3 rounded-xl font-medium
                         hover:bg-blue-900 transition-colors"
            >
              View in 3D →
            </button>
          </div>

          <div>
            <p className="text-xs text-slate-400 mb-2">Or try an example:</p>
            <div className="flex flex-col gap-1.5">
              {[
                ["Crosswind Quarter Zip", "https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html"],
                ["Gildan T-Shirt",        "https://www.ipromo.com/gildan-ultra-cotton-t-shirt.html"],
                ["Sport-Tek Polo",        "https://www.ipromo.com/sport-tek-micropique-sport-wick-polo.html"],
              ].map(([label, url]) => (
                <button
                  key={url}
                  onClick={() => window.location.href = `/?url=${encodeURIComponent(url)}`}
                  className="text-left text-sm text-ipromo-teal hover:underline px-1"
                >
                  → {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ViewerSkeleton() {
  return (
    <div className="w-full h-full rounded-2xl bg-slate-100 animate-pulse flex items-center justify-center">
      <p className="text-slate-400 text-sm">Loading product…</p>
    </div>
  )
}
