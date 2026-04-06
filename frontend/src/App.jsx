import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ConfiguratorPage from './pages/ConfiguratorPage'
import SharedViewPage from './pages/SharedViewPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ConfiguratorPage />} />
        <Route path="/share/:uuid" element={<SharedViewPage />} />
      </Routes>
    </BrowserRouter>
  )
}
