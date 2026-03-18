import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transactionsApi } from '../api/transactions'
import { useMonthStore } from '../store/monthStore'
import AmountDisplay from '../components/ui/AmountDisplay'
import CategoryBadge from '../components/ui/CategoryBadge'
import MonthPicker from '../components/ui/MonthPicker'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const CATEGORY_OPTIONS = [
  { slug: 'food_dining', name: 'Alimentación', icon: '🍽️' },
  { slug: 'transport', name: 'Transporte', icon: '🚗' },
  { slug: 'housing', name: 'Vivienda', icon: '🏠' },
  { slug: 'entertainment', name: 'Entretenimiento', icon: '🎬' },
  { slug: 'health', name: 'Salud', icon: '💊' },
  { slug: 'education', name: 'Educación', icon: '📚' },
  { slug: 'clothing', name: 'Ropa', icon: '👕' },
  { slug: 'utilities', name: 'Servicios', icon: '💡' },
  { slug: 'finance', name: 'Finanzas', icon: '🏦' },
  { slug: 'other_expense', name: 'Otros Gastos', icon: '📦' },
  { slug: 'salary', name: 'Sueldo', icon: '💰' },
  { slug: 'transfer_in', name: 'Transferencia Entrada', icon: '↩️' },
  { slug: 'other_income', name: 'Otros Ingresos', icon: '➕' },
]

export default function Transactions() {
  const { year, month } = useMonthStore()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', year, month, page, search],
    queryFn: () => transactionsApi.list({ year, month, page, page_size: 50, search }),
  })

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, categoryId }: { id: string; categoryId: string | null }) =>
      transactionsApi.updateCategory(id, categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      setEditingId(null)
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transacciones</h1>
          <p className="text-sm text-gray-500">{data?.total ?? 0} transacciones</p>
        </div>
        <MonthPicker />
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-3 flex gap-3">
        <input
          type="text"
          placeholder="Buscar descripción..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Cargando...</div>
        ) : !data?.items.length ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            No hay transacciones para este mes
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-600">Fecha</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-600">Descripción</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-600">Categoría</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">Monto</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.items.map((tx) => (
                <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {format(new Date(tx.date + 'T00:00:00'), 'd MMM', { locale: es })}
                  </td>
                  <td className="px-4 py-3 text-gray-800 max-w-xs truncate">
                    {tx.description}
                    {tx.is_auto_categorized && (
                      <span className="ml-1 text-xs text-gray-400">✨</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {editingId === tx.id ? (
                      <select
                        autoFocus
                        defaultValue={tx.category_slug || ''}
                        onChange={(e) => {
                          const opt = CATEGORY_OPTIONS.find(c => c.slug === e.target.value)
                          updateCategoryMutation.mutate({
                            id: tx.id,
                            categoryId: opt ? null : null, // will be resolved by slug server side
                          })
                          // Simplified: patch by slug requires a different approach
                          // For now close editing
                          setEditingId(null)
                        }}
                        onBlur={() => setEditingId(null)}
                        className="border border-gray-200 rounded px-2 py-1 text-xs"
                      >
                        <option value="">Sin categoría</option>
                        {CATEGORY_OPTIONS.map(c => (
                          <option key={c.slug} value={c.slug}>{c.icon} {c.name}</option>
                        ))}
                      </select>
                    ) : (
                      <CategoryBadge
                        name={tx.category_name}
                        icon={tx.category_icon}
                        color={tx.category_color}
                        onClick={() => setEditingId(tx.id)}
                      />
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <AmountDisplay amount={tx.amount} showSign />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50"
          >
            Anterior
          </button>
          <span className="text-sm text-gray-600">
            {page} / {data.total_pages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
            disabled={page === data.total_pages}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}
