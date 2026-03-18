import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import clsx from 'clsx'

interface Props {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

export default function FileDropzone({ onFiles, disabled }: Props) {
  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) onFiles(accepted)
  }, [onFiles])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf'],
    },
    disabled,
    multiple: true,
  })

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors',
        isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />
      <div className="text-4xl mb-3">{isDragActive ? '📂' : '📁'}</div>
      <p className="text-sm font-medium text-gray-700">
        {isDragActive ? 'Suelta los archivos aquí' : 'Arrastra archivos CSV o PDF aquí'}
      </p>
      <p className="text-xs text-gray-500 mt-1">o haz clic para seleccionar</p>
      <p className="text-xs text-gray-400 mt-3">
        Compatible: Banco de Chile, BCI, Santander, MACH, Tenpo, Mercado Pago
      </p>
    </div>
  )
}
