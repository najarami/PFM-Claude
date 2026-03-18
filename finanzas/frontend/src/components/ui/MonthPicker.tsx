import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { useMonthStore } from '../../store/monthStore'

export default function MonthPicker() {
  const { year, month, setMonth } = useMonthStore()

  const prev = () => {
    if (month === 1) setMonth(year - 1, 12)
    else setMonth(year, month - 1)
  }

  const next = () => {
    if (month === 12) setMonth(year + 1, 1)
    else setMonth(year, month + 1)
  }

  const label = format(new Date(year, month - 1, 1), 'MMMM yyyy', { locale: es })

  return (
    <div className="flex items-center gap-3">
      <button onClick={prev} className="p-1 rounded hover:bg-gray-100 text-gray-600">
        ‹
      </button>
      <span className="text-sm font-semibold capitalize w-36 text-center">{label}</span>
      <button onClick={next} className="p-1 rounded hover:bg-gray-100 text-gray-600">
        ›
      </button>
    </div>
  )
}
