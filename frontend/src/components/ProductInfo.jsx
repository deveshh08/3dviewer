import { useConfigurator } from '../store/configuratorStore'

export default function ProductInfo({ readOnly = false }) {
  const { productData } = useConfigurator()

  if (!productData) {
    return (
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
        <div className="h-3 bg-slate-100 rounded w-1/2" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
      <h2 className="text-base font-bold text-ipromo-navy leading-tight">{productData.name}</h2>
      <p className="text-xs text-slate-400 mt-0.5">Item # {productData.item_no}</p>
      <p className="text-sm font-semibold text-ipromo-teal mt-1">{productData.price}</p>
      {!readOnly && (
        <a
          href="https://www.ipromo.com"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-ipromo-navy underline mt-2 inline-block hover:text-ipromo-teal"
        >
          View on iPromo.com →
        </a>
      )}
    </div>
  )
}
