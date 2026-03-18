import type { BudgetStatus } from '../../api/types'
import { formatCLP } from './AmountDisplay'
import clsx from 'clsx'

interface Props {
  budget: BudgetStatus
}

export default function BudgetGauge({ budget }: Props) {
  const pct = Math.min(budget.pct_used, 100)
  const over = budget.pct_used > 100

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">{budget.icon}</span>
          <span className="text-sm font-medium text-gray-700">{budget.category_name}</span>
        </div>
        <span className={clsx('text-xs font-semibold', over ? 'text-red-600' : 'text-gray-500')}>
          {budget.pct_used.toFixed(0)}%
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className={clsx(
            'h-2 rounded-full transition-all',
            over ? 'bg-red-500' : pct >= 80 ? 'bg-yellow-400' : 'bg-green-500'
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>{formatCLP(budget.actual_amount)}</span>
        <span>/ {formatCLP(budget.budget_amount)}</span>
      </div>
    </div>
  )
}
