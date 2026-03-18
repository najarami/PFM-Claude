import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import FileDropzone from '../components/ui/FileDropzone'
import { accountsApi } from '../api/accounts'
import type { UploadResponse } from '../api/types'

export default function Upload() {
  const queryClient = useQueryClient()
  const [accountId, setAccountId] = useState('')
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState<Array<{ filename: string; result: UploadResponse | null; error: string | null }>>([])

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.list,
  })

  const handleFiles = async (files: File[]) => {
    if (!accountId) {
      alert('Selecciona una cuenta primero')
      return
    }
    setUploading(true)
    const newResults: Array<{ filename: string; result: UploadResponse | null; error: string | null }> = []

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('account_id', accountId)

      try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData })
        if (!res.ok) throw new Error(await res.text())
        const data: UploadResponse = await res.json()
        newResults.push({ filename: file.name, result: data, error: null })
      } catch (e) {
        newResults.push({ filename: file.name, result: null, error: String(e) })
      }
    }

    setResults(newResults)
    setUploading(false)
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
    queryClient.invalidateQueries({ queryKey: ['summary'] })
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cargar Cartola</h1>
        <p className="text-sm text-gray-500 mt-1">
          Sube tus cartolas bancarias o de tarjeta de crédito en formato CSV o PDF
        </p>
      </div>

      {/* Account selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
        <label className="block text-sm font-semibold text-gray-700">
          1. Selecciona la cuenta
        </label>
        <select
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="">-- Seleccionar cuenta --</option>
          {accounts.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name} ({acc.bank})
            </option>
          ))}
        </select>
        {accounts.length === 0 && (
          <p className="text-xs text-amber-600">
            No tienes cuentas registradas.{' '}
            <Link to="/accounts" className="underline font-medium hover:text-amber-800">
              Crea una aquí
            </Link>
            .
          </p>
        )}
      </div>

      {/* Dropzone */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
        <label className="block text-sm font-semibold text-gray-700">
          2. Sube los archivos
        </label>
        <FileDropzone onFiles={handleFiles} disabled={!accountId || uploading} />
        {uploading && (
          <div className="text-center text-sm text-blue-600 animate-pulse">
            Procesando archivos...
          </div>
        )}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-700">Resultados</h2>
          {results.map(({ filename, result, error }, i) => (
            <div
              key={i}
              className={`rounded-xl border p-4 ${error ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span>{error ? '❌' : '✅'}</span>
                <span className="text-sm font-medium text-gray-800">{filename}</span>
              </div>
              {error ? (
                <p className="text-xs text-red-600">{error}</p>
              ) : result ? (
                <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                  <div className="text-center">
                    <div className="font-bold text-gray-900 text-lg">{result.inserted}</div>
                    <div>importadas</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-gray-900 text-lg">{result.duplicates}</div>
                    <div>duplicadas</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-gray-900 text-lg">{result.total_parsed}</div>
                    <div>total leídas</div>
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
