export default function Navbar() {
  return (
    <header className="bg-ipromo-navy text-white px-6 py-3 flex items-center justify-between shadow-lg">
      <div className="flex items-center gap-3">
        <img src="/ipromo_logo.png" alt="iPromo" className="h-8 object-contain" />
        <div className="hidden sm:block border-l border-white/20 pl-3">
          <p className="text-xs text-white/60">27th Anniversary</p>
          <p className="text-sm font-semibold">3D Product Configurator</p>
        </div>
      </div>
      <a
        href="https://www.ipromo.com"
        target="_blank"
        rel="noreferrer"
        className="text-ipromo-teal text-xs underline hover:text-white transition-colors"
      >
        Visit iPromo.com →
      </a>
    </header>
  )
}
