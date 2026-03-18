import { type ViewMode } from '../../store/monthStore'

interface Props {
  mode: ViewMode
  currency: string
}

export default function ConversionBadge({ mode, currency }: Props) {
  if (mode === 'native') return null
  return (
    <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-0.5">
      <span>TC histórico</span>
      <span className="font-semibold">→ {currency}</span>
    </span>
  )
}
