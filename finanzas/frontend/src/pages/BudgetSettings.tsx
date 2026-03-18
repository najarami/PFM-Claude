import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgetApi } from '../api/budget'
import { useMonthStore } from '../store/monthStore'
import MonthPicker from '../components/ui/MonthPicker'
import CurrencyToggle from '../components/ui/CurrencyToggle'
import { formatAmount } from '../components/ui/AmountDisplay'

const CATEGORIES = [
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
]

export default function BudgetSettings() {
  const { year, month, currency, viewMode } = useMonthStore()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<Record<string, string>>({})
  const [useMonthSpecific, setUseMonthSpecific] = useState(false)

  const { data: budgets = [] } = useQuery({
    queryKey: ['budget', year, month, currency, viewMode],
    queryFn: () => budgetApi.list(year, month, currency, viewMode),
  })

  const saveMutation = useMutation({
    mutationFn: ({ slug, amount }: { slug: string; amount: number }) =>
      budgetApi.set(slug, amount, useMonthSpecific ? month : 0, useMonthSpecific ? year : 0, currency),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget'] })
    },
  })

  const budgetMap = Object.fromEntries(budgets.map((b: import('../api/types').BudgetStatus) => [b.category_slug, b.budget_amount]))

  const handleSave = (slug: string) => {
    const raw = editing[slug]
    if (!raw) return
    const amount = parseFloat(raw.replace(/\./g, '').replace(',', '.'))
    if (isNaN(amount) || amount < 0) return
    saveMutation.mutate({ slug, amount })
    setEditing(e => { const n = { ...e }; delete n[slug]; return n })
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Presupuesto</h1>
          <p className="text-sm text-gray-500 mt-1">Define cuánto quieres gastar por categoría</p>
        </div>
        <div className="flex items-center gap-3">
          <CurrencyToggle />
          <MonthPicker />
        </div>
      </div>

      {/* Currency indicator */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2 text-xs text-amber-700">
        Definiendo presupuesto en <strong>{currency}</strong>. Cambia la moneda arriba para gestionar presupuestos en USD o CLP por separado.
      </div>

      {/* Global vs monthly toggle */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
        <input
          type="checkbox"
          id="monthly"
          checked={useMonthSpecific}
          onChange={e => setUseMonthSpecific(e.target.checked)}
          className="w-4 h-4 text-blue-600"
        />
        <label htmlFor="monthly" className="text-sm text-blue-700">
          Aplicar solo al mes seleccionado (desactivado = presupuesto global para todos los meses)
        </label>
      </div>

      {/* Budget rows */}
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {CATEGORIES.map(cat => {
          const current = budgetMap[cat.slug]
          const isEditing = cat.slug in editing
          return (
            <div key={cat.slug} className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="text-lg">{cat.icon}</span>
                <span className="text-sm font-medium text-gray-700">{cat.name}</span>
              </div>
              <div className="flex items-center gap-2">
                {isEditing ? (
                  <>
                    <input
                      type="text"
                      value={editing[cat.slug]}
                      onChange={e => setEditing(d => ({ ...d, [cat.slug]: e.target.value }))}
                      placeholder="0"
                      className="w-32 border border-blue-300 rounded-lg px-3 py-1.5 text-sm text-right focus:outline-none focus:ring-2 focus:ring-blue-400"
                      onKeyDown={e => { if (e.key === 'Enter') handleSave(cat.slug) }}
                      autoFocus
                    />
                    <button
                      onClick={() => handleSave(cat.slug)}
                      className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700"
                    >
                      Guardar
                    </button>
                    <button
                      onClick={() => setEditing(e => { const n = { ...e }; delete n[cat.slug]; return n })}
                      className="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs rounded-lg hover:bg-gray-200"
                    >
                      Cancelar
                    </button>
                  </>
                ) : (
                  <>
                    <span className="text-sm font-mono text-gray-600">
                      {current ? formatAmount(current, currency) : <span className="text-gray-300">Sin presupuesto</span>}
                    </span>
                    <button
                      onClick={() => setEditing(e => ({ ...e, [cat.slug]: current ? String(Math.round(current)) : '' }))}
                      className="px-3 py-1.5 border border-gray-200 text-xs text-gray-600 rounded-lg hover:bg-gray-50"
                    >
                      {current ? 'Editar' : 'Agregar'}
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
