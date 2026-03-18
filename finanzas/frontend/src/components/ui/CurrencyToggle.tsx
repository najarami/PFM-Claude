import { useMonthStore, type Currency } from '../../store/monthStore'
import clsx from 'clsx'

const OPTIONS: { value: Currency; label: string; flag: string }[] = [
  { value: 'CLP', label: 'CLP', flag: '🇨🇱' },
  { value: 'USD', label: 'USD', flag: '🇺🇸' },
]

export default function CurrencyToggle() {
  const { currency, setCurrency } = useMonthStore()

  return (
    <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden bg-white">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => setCurrency(opt.value)}
          className={clsx(
            'flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold transition-colors',
            currency === opt.value
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 hover:bg-gray-50'
          )}
        >
          <span>{opt.flag}</span>
          <span>{opt.label}</span>
        </button>
      ))}
    </div>
  )
}
