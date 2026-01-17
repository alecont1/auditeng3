import { Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage, DashboardPage } from '@/pages'
import { ProtectedRoute } from '@/components/ProtectedRoute'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Catch all - redirect to dashboard (will bounce to login if not auth) */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
