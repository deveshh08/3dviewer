import { create } from 'zustand'

export const useConfigurator = create((set) => ({
  productUrl:    '',
  productData:   null,
  selectedColor: '#7ECECE',
  logoTexture:   null,
  logoZone:      'chest_left',
  decalTransform: { offsetX: 0.0, offsetY: 0.0, scale: 1.0, rotate: 0.0 },
  canvasSnapshot: null,

  setProductUrl:     (url)  => set({ productUrl: url }),
  setProductData:    (data) => set({ productData: data }),
  setColor:          (hex)  => set({ selectedColor: hex }),
  setLogoTexture:    (url)  => set({ logoTexture: url }),
  setLogoZone:       (zone) => set({ logoZone: zone }),
  setDecalTransform: (t)    => set({ decalTransform: t }),
  setCanvasSnapshot: (s)    => set({ canvasSnapshot: s }),
}))
