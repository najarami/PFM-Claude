import { useQuery } from '@tanstack/react-query'
import { useMonthStore } from '../store/monthStore'
import MonthPicker from '../components/ui/MonthPicker'
import CurrencyToggle from '../components/ui/CurrencyToggle'
import ExpensePieChart from '../components/charts/ExpensePieChart'
import AmountDisplay, { formatCLP } from '../components/ui/AmountDisplay'
import { summaryApi } from '../api/summary'

export default function MonthlyView() {
  const { year, month, currency } = useMonthStore()

  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', year, month, currency],
    queryFn: () => summaryApi.monthly(year, month, currency),
  })

  const incomeCategories = summary?.by_category.filter(c =>
    ['salary', 'transfer_in', 'other_income'].includes(c.category_slug)
  ) ?? []
  const expenseCategories = summary?.by_category.filter(c =>
    !['salary', 'transfer_in', 'other_income'].includes(c.category_slug)
  ) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Vista Mensual</h1>
        <div className="flex items-center gap-3">
          <CurrencyToggle />
          <MonthPicker />
        </div>
      </div>

      {isLoading ? (
        <div className="text-center text-gray-400 py-12">Cargando...</div>
      ) : summary ? (
        <>
          {/* Summary bar */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="text-xs text-green-600 font-semibold mb-1">INGRESOS</div>
              <div className="text-xl font-bold text-green-700">{formatCLP(summary.total_income)}</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="text-xs text-red-600 font-semibold mb-1">GASTOS</div>
              <div className="text-xl font-bold text-red-700">{formatCLP(summary.total_expense)}</div>
            </div>
            <div className={`border rounded-xl p-4 ${summary.net >= 0 ? 'bg-blue-50 border-blue-200' : 'bg-orange-50 border-orange-200'}`}>
              <div className="text-xs font-semibold mb-1">BALANCE</div>
              <div className="text-xl font-bold">
                <AmountDisplay amount={summary.net} showSign />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Expenses */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
              <h2 className="font-semibold text-gray-800">Gastos por categoría</h2>
              <ExpensePieChart data={expenseCategories} />
              <div className="space-y-2">
                {expenseCategories.map(cat => (
                  <div key={cat.category_slug} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }} />
                      <span>{cat.icon} {cat.category_name}</span>
                    </div>
                    <div className="flex gap-3 text-xs">
                      <span className="text-gray-400">{cat.pct_of_total}%</span>
                      <span className="font-medium text-red-600">{formatCLP(cat.amount)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Income */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
              <h2 className="font-semibold text-gray-800">Ingresos por categoría</h2>
              <ExpensePieChart data={incomeCategories} />
              <div className="space-y-2">
                {incomeCategories.map(cat => (
                  <div key={cat.category_slug} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }} />
                      <span>{cat.icon} {cat.category_name}</span>
                    </div>
                    <span className="text-xs font-medium text-green-600">{formatCLP(cat.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center text-gray-400 py-12 text-sm">No hay datos para este mes</div>
      )}
    </div>
  )
}
