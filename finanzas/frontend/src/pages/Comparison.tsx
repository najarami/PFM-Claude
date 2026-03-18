import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonthStore } from '../store/monthStore'
import { summaryApi } from '../api/summary'
import IncomeExpenseBar from '../components/charts/IncomeExpenseBar'
import CurrencyToggle from '../components/ui/CurrencyToggle'
import { formatCLP } from '../components/ui/AmountDisplay'

function getLast12Months(): Array<{ year: number; month: number }> {
  const result = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    result.push({ year: d.getFullYear(), month: d.getMonth() + 1 })
  }
  return result.reverse()
}

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

export default function Comparison() {
  const last12 = getLast12Months()
  const [selected, setSelected] = useState(last12.slice(-6))
  const { currency } = useMonthStore()

  const { data: comparison = [], isLoading } = useQuery({
    queryKey: ['comparison', selected, currency],
    queryFn: () => summaryApi.comparison(selected, currency),
    enabled: selected.length > 0,
  })

  const toggleMonth = (m: { year: number; month: number }) => {
    const exists = selected.some(s => s.year === m.year && s.month === m.month)
    if (exists) {
      setSelected(selected.filter(s => !(s.year === m.year && s.month === m.month)))
    } else if (selected.length < 12) {
      setSelected([...selected, m].sort((a, b) => a.year !== b.year ? a.year - b.year : a.month - b.month))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Comparativo Mensual</h1>
        <CurrencyToggle />
      </div>

      {/* Month selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <p className="text-xs text-gray-500 mb-3">Selecciona hasta 12 meses para comparar</p>
        <div className="flex flex-wrap gap-2">
          {last12.map(m => {
            const isSelected = selected.some(s => s.year === m.year && s.month === m.month)
            return (
              <button
                key={`${m.year}-${m.month}`}
                onClick={() => toggleMonth(m)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  isSelected
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {MONTH_NAMES[m.month - 1]} {m.year}
              </button>
            )
          })}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center text-gray-400 py-8">Cargando...</div>
      ) : comparison.length > 0 ? (
        <>
          {/* Bar chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Ingresos vs Gastos</h2>
            <IncomeExpenseBar data={comparison} />
          </div>

          {/* Summary table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Mes</th>
                  <th className="px-4 py-3 text-right font-semibold text-green-600">Ingresos</th>
                  <th className="px-4 py-3 text-right font-semibold text-red-600">Gastos</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {comparison.map(m => (
                  <tr key={`${m.year}-${m.month}`} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-700">
                      {MONTH_NAMES[m.month - 1]} {m.year}
                    </td>
                    <td className="px-4 py-3 text-right text-green-600 font-mono">
                      {formatCLP(m.total_income)}
                    </td>
                    <td className="px-4 py-3 text-right text-red-600 font-mono">
                      {formatCLP(m.total_expense)}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono font-semibold ${m.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {m.net >= 0 ? '+' : ''}{formatCLP(m.net)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="text-center text-gray-400 py-8 text-sm">
          Selecciona meses para comparar
        </div>
      )}
    </div>
  )
}
