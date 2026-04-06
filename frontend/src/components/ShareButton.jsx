import { useState } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'
import { useConfigurator } from '../store/configuratorStore'
import { Link2, Copy, Check } from 'lucide-react'

export default function ShareButton() {
  const { selectedColor, logoTexture, logoTransform, productUrl, productData } = useConfigurator()
  const [shareUrl, setShareUrl] = useState('')
  const [copied, setCopied]   = useState(false)
  const [loading, setLoading] = useState(false)

  const handleShare = async () => {
    setLoading(true)
    try {
      const { data } = await client.post('/api/configs/', {
        product_url: productUrl,
        color:       selectedColor,
        logo_url:    logoTexture,
        logo_pos:    logoTransform,
        extra_data:  productData,
      })
      const url = `${window.location.origin}/share/${data.id}`
      setShareUrl(url)
      await navigator.clipboard.writeText(url)
      setCopied(true)
      toast.success('Link copied to clipboard!')
      setTimeout(() => setCopied(false), 3000)
    } catch {
      toast.error('Could not generate share link')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleShare}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 bg-ipromo-navy text-white py-2.5 px-4 rounded-xl font-medium text-sm hover:bg-blue-900 transition-colors disabled:opacity-60"
      >
        <Link2 size={16} />
        {loading ? 'Generating…' : 'Get Shareable Link'}
      </button>

      {shareUrl && (
        <div className="flex items-center gap-2 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
          <span className="flex-1 text-xs text-slate-600 truncate">{shareUrl}</span>
          <button
            onClick={() => { navigator.clipboard.writeText(shareUrl); setCopied(true) }}
            className="text-ipromo-teal hover:text-teal-700 flex-shrink-0"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        </div>
      )}
    </div>
  )
}
