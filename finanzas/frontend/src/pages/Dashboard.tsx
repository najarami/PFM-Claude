import { useQuery } from '@tanstack/react-query'
import { useMonthStore } from '../store/monthStore'
import MonthPicker from '../components/ui/MonthPicker'
import CurrencyToggle from '../components/ui/CurrencyToggle'
import ConversionBadge from '../components/ui/ConversionBadge'
import BudgetGauge from '../components/ui/BudgetGauge'
import AmountDisplay, { formatAmount } from '../components/ui/AmountDisplay'
import ExpensePieChart from '../components/charts/ExpensePieChart'
import { summaryApi } from '../api/summary'
import { budgetApi } from '../api/budget'

interface KPICardProps {
  title: string
  value: number
  icon: string
  color: 'green' | 'red' | 'blue'
  currency: string
}

function KPICard({ title, value, icon, color, currency }: KPICardProps) {
  const colors = {
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  }
  return (
    <div className={`rounded-xl border p-5 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xl">{icon}</span>
        <span className="text-xs font-semibold uppercase tracking-wide opacity-70">{title}</span>
      </div>
      <div className="text-2xl font-bold">{formatAmount(value, currency)}</div>
    </div>
  )
}

export default function Dashboard() {
  const { year, month, currency, viewMode } = useMonthStore()

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['summary', year, month, currency, viewMode],
    queryFn: () => summaryApi.monthly(year, month, currency, viewMode),
  })

  const { data: budgets = [] } = useQuery({
    queryKey: ['budget', year, month, currency, viewMode],
    queryFn: () => budgetApi.list(year, month, currency, viewMode),
  })

  const displayCurrency = summary?.display_currency ?? currency
  const expenseCategories = summary?.by_category.filter((c: { category_slug: string }) => !['salary', 'transfer_in', 'other_income'].includes(c.category_slug)) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <ConversionBadge mode={viewMode} currency={displayCurrency} />
        </div>
        <div className="flex items-center gap-3">
          <CurrencyToggle />
          <MonthPicker />
        </div>
      </div>

      {loadingSummary ? (
        <div className="text-center text-gray-400 py-12">Cargando...</div>
      ) : summary ? (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-3 gap-4">
            <KPICard title="Ingresos" value={summary.total_income} icon="💰" color="green" currency={displayCurrency} />
            <KPICard title="Gastos" value={summary.total_expense} icon="💸" color="red" currency={displayCurrency} />
            <KPICard title="Balance" value={summary.net} icon="⚖️" color="blue" currency={displayCurrency} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Expense breakdown chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <ExpensePieChart
                data={expenseCategories}
                title="Gastos por categoría"
              />
            </div>

            {/* Category breakdown table */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Detalle por categoría</h3>
              <div className="space-y-2 max-h-52 overflow-y-auto">
                {summary.by_category.map(cat => (
                  <div key={cat.category_slug} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span>{cat.icon}</span>
                      <span className="text-gray-700">{cat.category_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-gray-400">{cat.pct_of_total}%</span>
                      <AmountDisplay amount={-cat.amount} currency={displayCurrency} className="text-xs" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Budget gauges */}
          {budgets.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Presupuesto</h2>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {budgets.map(b => (
                  <BudgetGauge key={b.category_slug} budget={b} />
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center text-gray-400 py-12">
          <div className="text-4xl mb-3">📭</div>
          <p className="text-sm">No hay datos para este mes.</p>
          <p className="text-xs mt-1">Sube una cartola para comenzar.</p>
        </div>
      )}
    </div>
  )
}
