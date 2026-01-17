import { Link, useLocation } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

// Label mapping for route segments
const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  upload: 'Upload',
  analyses: 'Analyses',
  reports: 'Reports',
  analysis: 'Analysis',
  report: 'Report',
}

export function Breadcrumbs() {
  const location = useLocation()

  // Parse pathname into segments
  const segments = location.pathname
    .split('/')
    .filter(Boolean)

  // Build breadcrumb items
  const breadcrumbs = segments.map((segment, index) => {
    // Build path up to this segment
    const path = '/' + segments.slice(0, index + 1).join('/')

    // Get label (use mapping or capitalize)
    const label = routeLabels[segment] || formatSegment(segment)

    // Is this the last (current) item?
    const isLast = index === segments.length - 1

    return { path, label, isLast }
  })

  // Handle root path
  if (segments.length === 0) {
    return (
      <nav className="flex items-center text-sm text-muted-foreground">
        <Home className="h-4 w-4" />
      </nav>
    )
  }

  return (
    <nav className="flex items-center text-sm">
      {/* Home icon */}
      <Link
        to="/dashboard"
        className="text-muted-foreground hover:text-foreground transition-colors"
      >
        <Home className="h-4 w-4" />
      </Link>

      {/* Breadcrumb items */}
      {breadcrumbs.map((item) => (
        <div key={item.path} className="flex items-center">
          <ChevronRight className="h-4 w-4 mx-2 text-muted-foreground" />
          {item.isLast ? (
            <span className="font-medium text-foreground">
              {item.label}
            </span>
          ) : (
            <Link
              to={item.path}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {item.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  )
}

// Format segment: capitalize first letter or handle IDs
function formatSegment(segment: string): string {
  // Check if segment looks like an ID (UUID, number, etc.)
  if (/^[0-9a-f-]{8,}$/i.test(segment) || /^\d+$/.test(segment)) {
    // Return shortened version for IDs
    return segment.length > 8 ? `${segment.slice(0, 8)}...` : segment
  }

  // Capitalize first letter and replace hyphens with spaces
  return segment
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
