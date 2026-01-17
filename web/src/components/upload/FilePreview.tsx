import { FileText, Image, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatFileSize, getFileTypeLabel } from '@/lib/file-utils'

interface FilePreviewProps {
  file: File
  onRemove: () => void
}

export function FilePreview({ file, onRemove }: FilePreviewProps) {
  const isPdf = file.type === 'application/pdf'
  const Icon = isPdf ? FileText : Image

  return (
    <Card className="p-4">
      <div className="flex items-center gap-4">
        {/* File icon */}
        <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center bg-muted rounded-lg">
          <Icon className="w-6 h-6 text-muted-foreground" />
        </div>

        {/* File info */}
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate" title={file.name}>
            {file.name}
          </p>
          <p className="text-sm text-muted-foreground">
            {formatFileSize(file.size)} &bull; {getFileTypeLabel(file.type)}
          </p>
        </div>

        {/* Remove button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onRemove}
          className="flex-shrink-0"
          aria-label="Remove file"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </Card>
  )
}
