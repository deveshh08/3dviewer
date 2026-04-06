import { useConfigurator } from '../store/configuratorStore'

const COLOR_MAP = {
  "Aqua":     "#7ECECE",
  "Pink":     "#F08080",
  "Tan":      "#C4A882",
  "Black":    "#1A1A1A",
  "Silver":   "#B0B0B0",
  "White":    "#F5F5F5",
  "Navy":     "#1B2A6B",
  "Graphite": "#4A4A4A",
  "Purple":   "#6A0DAD",
  "Red":      "#CC2020",
}

export default function ColorPicker() {
  const { selectedColor, setColor } = useConfigurator()

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
      <h3 className="text-sm font-semibold text-ipromo-navy mb-3">
        1. Choose Color
        <span className="ml-2 text-ipromo-teal font-normal">
          {Object.entries(COLOR_MAP).find(([, v]) => v === selectedColor)?.[0] ?? ''}
        </span>
      </h3>
      <div className="flex flex-wrap gap-2">
        {Object.entries(COLOR_MAP).map(([name, hex]) => (
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
