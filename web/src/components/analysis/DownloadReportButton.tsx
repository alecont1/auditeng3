import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { downloadReport } from '@/services/analysis'

interface DownloadReportButtonProps {
  analysisId: string
  disabled?: boolean
}

export function DownloadReportButton({
  analysisId,
  disabled,
}: DownloadReportButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleDownload = async () => {
    setIsLoading(true)
    try {
      await downloadReport(analysisId)
      toast.success('Report downloaded')
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to download report'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      variant="outline"
      onClick={handleDownload}
      disabled={disabled || isLoading}
    >
      {isLoading ? (
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      ) : (
        <Download className="mr-2 h-4 w-4" />
      )}
      {isLoading ? 'Downloading...' : 'Download Report'}
    </Button>
  )
}
