import { useState } from 'react'
import { Toaster } from 'react-hot-toast'
import Viewport3D from './components/Viewport3D'
import Sidebar from './components/Sidebar'
import Toolbar from './components/Toolbar'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen w-screen bg-slate-900">
      <Toaster position="bottom-right" />
      {sidebarOpen && <div className="w-[360px] border-r border-gray-700"><Sidebar /></div>}
      <div className="flex-1 flex flex-col">
        <Toolbar sidebarOpen={sidebarOpen} onToggleSidebar={() => setSidebarOpen((v) => !v)} />
        <div className="flex-1 relative">
          <Viewport3D />
        </div>
      </div>
    </div>
  )
}

export default App
