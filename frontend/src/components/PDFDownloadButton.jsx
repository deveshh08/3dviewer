import { useState } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { FileDown } from 'lucide-react'

const HEX_TO_NAME = {
  "#7ECECE": "Aqua", "#F08080": "Pink", "#C4A882": "Tan",
  "#1A1A1A": "Black", "#B0B0B0": "Silver", "#F5F5F5": "White",
  "#1B2A6B": "Navy", "#4A4A4A": "Graphite", "#6A0DAD": "Purple", "#CC2020": "Red"
}

export default function PDFDownloadButton({ canvasRef }) {
  const { selectedColor, productData } = useConfigurator()
  const [loading, setLoading] = useState(false)

  const handleDownload = async () => {
    setLoading(true)
    try {
      let snapshot = null
      if (canvasRef?.current) {
        snapshot = canvasRef.current.toDataURL('image/png')
      }

      const { data } = await client.post('/api/pdf/download', {
        product_name: productData?.name    ?? 'Crosswind Quarter Zip Sweatshirt',
        item_no:      productData?.item_no ?? 'IP-276-9359',
        price:        productData?.price   ?? '$43.99 – $51.99',
        color:        HEX_TO_NAME[selectedColor] ?? selectedColor,
        snapshot_url: snapshot,
      }, { responseType: 'blob' })

      const url = URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'ipromo_mockup.pdf'
      a.click()
      toast.success('PDF downloaded!')
    } catch {
      toast.error('PDF generation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="w-full flex items-center justify-center gap-2 bg-ipromo-teal text-white py-2.5 px-4 rounded-xl font-medium text-sm hover:bg-teal-600 transition-colors disabled:opacity-60"
    >
      <FileDown size={16} />
      {loading ? 'Generating PDF…' : 'Download PDF Mockup'}
    </button>
  )
}
