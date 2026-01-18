import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { FileDropzone, FilePreview, UploadProgress } from '@/components/upload'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useUpload, useTaskStatus } from '@/hooks'

export function UploadPage() {
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)

  const { upload, isUploading, progress, reset } = useUpload()

  const { data: taskStatus } = useTaskStatus({
    taskId,
    onCompleted: (data) => {
      toast.success('Analysis complete!')
      navigate(`/analysis/${data.result?.analysis_id}`)
    },
    onFailed: (error) => {
      toast.error(error)
      reset()
      setTaskId(null)
      setSelectedFile(null)
    },
  })

  const handleSubmit = async () => {
    if (!selectedFile) return
    try {
      const result = await upload(selectedFile)
      setTaskId(result.task_id)
    } catch (error) {
      // Provide specific error messages
      const errorMessage = error instanceof Error ? error.message : ''
      if (errorMessage.toLowerCase().includes('network') ||
          errorMessage.toLowerCase().includes('timeout') ||
          error instanceof TypeError) {
        toast.error('Unable to connect. Please check your internet and try again.')
      } else if (errorMessage.includes('413') || errorMessage.toLowerCase().includes('too large')) {
        toast.error('File is too large. Maximum size is 50MB.')
      } else {
        toast.error('Upload failed. Please try again.')
      }
    }
  }

  const isProcessing = isUploading || !!taskId

  // Show progress during upload/processing
  if (isProcessing) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Uploading Document</h1>
          <p className="text-muted-foreground">
            Please wait while we process your file
          </p>
        </div>
        <UploadProgress
          uploadProgress={progress}
          taskStatus={taskStatus?.status}
          taskProgress={taskStatus?.progress}
        />
      </div>
    )
  }

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
          <Button className="w-full" size="lg" onClick={handleSubmit}>
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
