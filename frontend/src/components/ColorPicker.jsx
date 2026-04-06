import { useConfigurator } from '../store/configuratorStore'

const FALLBACK_COLORS = [
  { name: "Black",    hex: "#1A1A1A" },
  { name: "Navy",     hex: "#1B2A6B" },
  { name: "White",    hex: "#F5F5F5" },
  { name: "Graphite", hex: "#4A4A4A" },
  { name: "Red",      hex: "#CC2020" },
]

export default function ColorPicker() {
  const { selectedColor, setColor, productData } = useConfigurator()
  const colors = productData?.colors ?? FALLBACK_COLORS

  const selectedName = colors.find(c => c.hex === selectedColor)?.name ?? ''

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
      <h3 className="text-sm font-semibold text-ipromo-navy mb-3">
        1. Choose Color
        <span className="ml-2 text-ipromo-teal font-normal">{selectedName}</span>
      </h3>
      <div className="flex flex-wrap gap-2">
        {colors.map(({ name, hex }) => (
          <button
            key={name}
            title={name}
            onClick={() => setColor(hex)}
            className={`w-8 h-8 rounded-full border-2 transition-all duration-150 shadow-sm hover:scale-110
              ${selectedColor === hex
                ? 'border-ipromo-teal scale-110 ring-2 ring-ipromo-teal ring-offset-1'
                : 'border-white'}`}
            style={{ backgroundColor: hex }}
          />
        ))}
      </div>
    </div>
  )
}
