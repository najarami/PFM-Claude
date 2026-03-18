import clsx from 'clsx'

interface Props {
  amount: number
  showSign?: boolean
  currency?: string
  className?: string
}

export function formatCLP(amount: number): string {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    maximumFractionDigits: 0,
  }).format(Math.abs(amount))
}

export function formatUSD(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(amount))
}

export function formatAmount(amount: number, currency = 'CLP'): string {
  return currency === 'USD' ? formatUSD(amount) : formatCLP(amount)
}

export default function AmountDisplay({ amount, showSign = false, currency = 'CLP', className }: Props) {
  const isPositive = amount >= 0
  return (
    <span
      className={clsx(
        'font-mono font-medium tabular-nums',
        isPositive ? 'text-green-600' : 'text-red-600',
        className
      )}
    >
      {showSign && (isPositive ? '+' : '-')}
      {formatAmount(amount, currency)}
    </span>
  )
}
