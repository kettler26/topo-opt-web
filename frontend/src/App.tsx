import { useState } from 'react'
import { Toaster } from 'react-hot-toast'
import Viewport3D from './components/Viewport3D'
import Sidebar from './components/Sidebar'
import Toolbar from './components/Toolbar'

function App() {
  return (
    <div className="flex h-screen w-screen bg-slate-900">
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#e2e8f0',
            border: '1px solid #334155',
          },
        }}
      />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <Toolbar />

        {/* 3D Viewport */}
        <div className="flex-1 relative">
          <Viewport3D />
        </div>
      </div>
    </div>
  )
}

export default App
