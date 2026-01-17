import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { submitAnalysis } from '@/services/analysis'
import type { SubmitAnalysisResponse } from '@/types'

interface UseUploadResult {
  upload: (file: File) => Promise<SubmitAnalysisResponse>
  isUploading: boolean
  progress: number
  error: Error | null
  reset: () => void
}

export function useUpload(): UseUploadResult {
  const [progress, setProgress] = useState(0)

  const mutation = useMutation({
    mutationFn: (file: File) => submitAnalysis(file, setProgress),
    onMutate: () => setProgress(0),
  })

  return {
    upload: mutation.mutateAsync,
    isUploading: mutation.isPending,
    progress,
    error: mutation.error,
    reset: () => {
      mutation.reset()
      setProgress(0)
    },
  }
}
