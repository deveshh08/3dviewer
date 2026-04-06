import { create } from 'zustand'

export const useConfigurator = create((set) => ({
  productUrl:    '',
  productData:   null,
  selectedColor: '#7ECECE',
  logoTexture:   null,
  logoTransform: { x: 0, y: 0, s: 0.18 },

  setProductUrl:    (url)  => set({ productUrl: url }),
  setProductData:   (data) => set({ productData: data }),
  setColor:         (hex)  => set({ selectedColor: hex }),
  setLogoTexture:   (url)  => set({ logoTexture: url }),
  setLogoTransform: (t)    => set({ logoTransform: t }),
}))
