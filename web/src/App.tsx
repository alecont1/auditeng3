import { Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage, DashboardPage, UploadPage, AnalysisDetailsPage, AuditTrailPage } from '@/pages'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { MainLayout } from '@/components/layout'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes with layout */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <MainLayout>
              <DashboardPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <MainLayout>
              <UploadPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/analyses/:id"
        element={
          <ProtectedRoute>
            <MainLayout>
              <AnalysisDetailsPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/analyses/:analysisId/audit"
        element={
          <ProtectedRoute>
            <MainLayout>
              <AuditTrailPage />
            </MainLayout>
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
