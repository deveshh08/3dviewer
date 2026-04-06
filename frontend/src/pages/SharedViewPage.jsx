import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import client from '../api/client'
import { useConfigurator } from '../store/configuratorStore'
import Viewer3D from '../components/Viewer3D'
import ProductInfo from '../components/ProductInfo'

export default function SharedViewPage() {
  const { uuid } = useParams()
  const { setColor, setLogoTexture, setLogoTransform, setProductData, productData } = useConfigurator()

  useEffect(() => {
    client.get(`/api/configs/${uuid}`).then(({ data }) => {
      if (data.color)      setColor(data.color)
      if (data.logo_url)   setLogoTexture(data.logo_url)
      if (data.logo_pos)   setLogoTransform(data.logo_pos)
      if (data.extra_data) setProductData(data.extra_data)
    })
  }, [uuid])

  // Step 31: og meta tags for social previews
  useEffect(() => {
    const productName = productData?.name ?? 'iPromo 3D Product Mockup'
    document.title = `${productName} — iPromo 3D Configurator`

    const setMeta = (property, content) => {
      let el = document.querySelector(`meta[property='${property}']`)
      if (!el) {
        el = document.createElement('meta')
        el.setAttribute('property', property)
        document.head.appendChild(el)
      }
      el.setAttribute('content', content)
    }

    setMeta('og:title', `${productName} — Custom iPromo Mockup`)
    setMeta('og:description', `View this custom ${productName} configured with iPromo's 3D Configurator. Order branded merchandise at ipromo.com`)
    setMeta('og:url', window.location.href)
    setMeta('og:type', 'website')
    setMeta('og:image', 'https://www.ipromo.com/media/logo/stores/1/iPromo_27th_Anniversary_v2.png')
  }, [productData])

  return (
    <div className="min-h-screen bg-ipromo-light flex flex-col">
      <div className="bg-ipromo-navy text-white text-center py-2 text-sm">
        👀 You're viewing a custom iPromo product mockup —{' '}
        <a href="https://www.ipromo.com" className="text-ipromo-teal underline ml-1">
          Order yours at iPromo.com
        </a>
      </div>

      <div className="flex-1 flex items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-[380px] sm:h-[500px] relative">
            <Viewer3D />
          </div>
          <ProductInfo readOnly />
        </div>
      </div>
    </div>
  )
}
