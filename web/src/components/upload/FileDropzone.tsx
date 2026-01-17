import { useState, useRef } from 'react'
import type { DragEvent, ChangeEvent } from 'react'
import { Upload } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { validateFile, ALLOWED_TYPES } from '@/lib/file-utils'

interface FileDropzoneProps {
  onFileSelect: (file: File) => void
  disabled?: boolean
}

export function FileDropzone({ onFileSelect, disabled }: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragOver(true)
    }
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    if (disabled) return

    const file = e.dataTransfer?.files[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleFile = (file: File) => {
    const result = validateFile(file)
    if (!result.valid) {
      toast.error(result.error)
      return
    }
    onFileSelect(file)
  }

  const handleClick = () => {
    if (!disabled && inputRef.current) {
      inputRef.current.click()
    }
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFile(file)
    }
    // Reset input to allow selecting the same file again
    e.target.value = ''
  }

  return (
    <div
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'relative flex flex-col items-center justify-center w-full h-64',
        'border-2 border-dashed rounded-lg',
        'transition-all duration-200 ease-in-out',
        'cursor-pointer',
        // Default state
        'border-muted-foreground/25 bg-muted/50 hover:bg-muted/80',
        // Drag over state
        isDragOver && 'border-primary bg-primary/5 scale-[1.02]',
        // Disabled state
        disabled && 'opacity-50 cursor-not-allowed hover:bg-muted/50'
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED_TYPES.join(',')}
        onChange={handleInputChange}
        className="hidden"
        disabled={disabled}
      />

      <Upload
        className={cn(
          'w-12 h-12 mb-4 transition-colors',
          isDragOver ? 'text-primary' : 'text-muted-foreground'
        )}
      />

      <p className={cn(
        'text-lg font-medium mb-1 transition-colors',
        isDragOver ? 'text-primary' : 'text-foreground'
      )}>
        Drag and drop your file here
      </p>

      <p className="text-sm text-muted-foreground">
        or click to browse
      </p>

      <p className="text-xs text-muted-foreground mt-4">
        PDF, JPEG, PNG, WebP up to 50MB
      </p>
    </div>
  )
}
