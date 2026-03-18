import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import type { MonthComparison } from '../../api/types'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { formatCLP } from '../ui/AmountDisplay'

interface Props {
  data: MonthComparison[]
}

export default function IncomeExpenseBar({ data }: Props) {
  const chartData = data.map(d => ({
    name: format(new Date(d.year, d.month - 1, 1), 'MMM yy', { locale: es }),
    Ingresos: d.total_income,
    Gastos: d.total_expense,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
        <Tooltip formatter={(value: number) => [formatCLP(value), '']} />
        <Legend />
        <Bar dataKey="Ingresos" fill="#22C55E" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Gastos" fill="#EF4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
