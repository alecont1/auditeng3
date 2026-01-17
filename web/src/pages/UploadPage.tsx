import { useState } from 'react'
import { FileDropzone, FilePreview } from '@/components/upload'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Upload Document</h1>
        <p className="text-muted-foreground">
          Upload a PDF or image for automated analysis
        </p>
      </div>

      {!selectedFile ? (
        <FileDropzone onFileSelect={setSelectedFile} />
      ) : (
        <div className="space-y-4">
          <FilePreview file={selectedFile} onRemove={() => setSelectedFile(null)} />
          <Button className="w-full" size="lg">
            Start Analysis
          </Button>
        </div>
      )}

      {/* Info card about supported files */}
      <Card className="p-4">
        <h3 className="font-medium mb-2">Supported files</h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>PDF documents (up to 50MB)</li>
          <li>Images: JPEG, PNG, WebP</li>
        </ul>
      </Card>
    </div>
  )
}
