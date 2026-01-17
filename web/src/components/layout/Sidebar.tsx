import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { LayoutDashboard, Upload, FileSearch, FileText, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Upload', href: '/upload', icon: Upload },
  { name: 'Analyses', href: '/analyses', icon: FileSearch },
  { name: 'Reports', href: '/reports', icon: FileText },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-60 bg-card border-r',
          'transform transition-transform duration-200 ease-in-out',
          'lg:hidden',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b">
          <span className="text-lg font-semibold">AuditEng</span>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="lg:hidden"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close sidebar</span>
          </Button>
        </div>
        <nav className="p-4 space-y-1">
          <SidebarNav onLinkClick={onClose} />
        </nav>
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-50 lg:flex lg:w-60 lg:flex-col">
        <div className="flex h-full flex-col bg-card border-r">
          {/* Logo */}
          <div className="flex h-16 items-center px-6 border-b">
            <span className="text-lg font-semibold">AuditEng</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            <SidebarNav />
          </nav>

          {/* Footer */}
          <div className="p-4 border-t">
            <p className="text-xs text-muted-foreground">
              AuditEng v2.0
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}

interface SidebarNavProps {
  onLinkClick?: () => void
}

function SidebarNav({ onLinkClick }: SidebarNavProps) {
  return (
    <>
      {navigation.map((item) => (
        <NavLink
          key={item.name}
          to={item.href}
          onClick={onLinkClick}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors',
              isActive
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
            )
          }
        >
          <item.icon className="h-4 w-4" />
          {item.name}
        </NavLink>
      ))}
    </>
  )
}
