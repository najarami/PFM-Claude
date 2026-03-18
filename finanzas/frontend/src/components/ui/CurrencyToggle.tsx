import { useMonthStore, type Currency, type ViewMode } from '../../store/monthStore'
import clsx from 'clsx'

const CURRENCY_OPTIONS: { value: Currency; label: string; flag: string }[] = [
  { value: 'CLP', label: 'CLP', flag: '🇨🇱' },
  { value: 'USD', label: 'USD', flag: '🇺🇸' },
]

const MODE_OPTIONS: { value: ViewMode; label: string }[] = [
  { value: 'native', label: 'Nativo' },
  { value: 'converted', label: 'Convertido' },
]

export default function CurrencyToggle() {
  const { currency, setCurrency, viewMode, setViewMode } = useMonthStore()

  return (
    <div className="flex items-center gap-2">
      {/* View mode toggle */}
      <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden bg-white">
        {MODE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setViewMode(opt.value)}
            className={clsx(
              'px-3 py-1.5 text-xs font-semibold transition-colors',
              viewMode === opt.value
                ? 'bg-indigo-600 text-white'
                : 'text-gray-600 hover:bg-gray-50'
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Currency selector — always visible to set the target currency */}
      <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden bg-white">
        {CURRENCY_OPTIONS.map((opt) => (
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
    </div>
  )
}
