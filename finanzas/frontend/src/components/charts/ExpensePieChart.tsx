import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import type { CategoryBreakdown } from '../../api/types'
import { formatCLP } from '../ui/AmountDisplay'

interface Props {
  data: CategoryBreakdown[]
  title?: string
}

export default function ExpensePieChart({ data, title }: Props) {
  const filtered = data.filter(d => d.amount > 0).slice(0, 8)

  if (!filtered.length) {
    return <div className="text-center text-gray-400 text-sm py-8">Sin datos</div>
  }

  return (
    <div>
      {title && <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>}
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={filtered}
            dataKey="amount"
            nameKey="category_name"
            cx="50%"
            cy="50%"
            outerRadius={90}
            innerRadius={50}
          >
            {filtered.map((entry, i) => (
              <Cell key={i} fill={entry.color || '#6B7280'} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [formatCLP(value), '']}
            labelFormatter={(label) => label}
          />
          <Legend
            formatter={(value) => <span className="text-xs">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
