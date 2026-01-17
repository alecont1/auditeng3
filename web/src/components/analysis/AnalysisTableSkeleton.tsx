import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

const SKELETON_ROWS = 5

export function AnalysisTableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Equipment Tag</TableHead>
          <TableHead>Test Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Verdict</TableHead>
          <TableHead>Compliance</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Created</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: SKELETON_ROWS }).map((_, index) => (
          <TableRow key={index}>
            <TableCell>
              <Skeleton className="h-4 w-24" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-20" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-16 rounded-full" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-20 rounded-full" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-12" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-12" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-24" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
