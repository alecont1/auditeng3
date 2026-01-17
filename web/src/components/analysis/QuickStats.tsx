import { FileText, Clock, CheckCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface QuickStatsProps {
  totalCount: number
  pendingCount: number
  completedTodayCount: number
  isLoading: boolean
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  colorClass?: string
  isLoading: boolean
}

function StatCard({ title, value, icon, colorClass, isLoading }: StatCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-6 w-12" />
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className={cn(
            'flex h-10 w-10 items-center justify-center rounded-lg',
            colorClass ?? 'bg-muted text-muted-foreground'
          )}>
            {icon}
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-semibold">{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function QuickStats({
  totalCount,
  pendingCount,
  completedTodayCount,
  isLoading,
}: QuickStatsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <StatCard
        title="Total Analyses"
        value={totalCount}
        icon={<FileText className="h-5 w-5" />}
        colorClass="bg-primary/10 text-primary"
        isLoading={isLoading}
      />
      <StatCard
        title="Pending Review"
        value={pendingCount}
        icon={<Clock className="h-5 w-5" />}
        colorClass={pendingCount > 0 ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/20 dark:text-amber-400' : 'bg-muted text-muted-foreground'}
        isLoading={isLoading}
      />
      <StatCard
        title="Completed Today"
        value={completedTodayCount}
        icon={<CheckCircle className="h-5 w-5" />}
        colorClass="bg-green-100 text-green-600 dark:bg-green-900/20 dark:text-green-400"
        isLoading={isLoading}
      />
    </div>
  )
}
