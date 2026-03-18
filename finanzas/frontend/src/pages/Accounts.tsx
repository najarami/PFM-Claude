import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsApi } from '../api/accounts'

const BANKS = [
  { value: 'banco_chile', label: 'Banco de Chile' },
  { value: 'bci', label: 'BCI' },
  { value: 'santander', label: 'Santander' },
  { value: 'mach', label: 'MACH' },
  { value: 'tenpo', label: 'Tenpo' },
  { value: 'mercado_pago', label: 'Mercado Pago' },
  { value: 'bank_of_america', label: 'Bank of America' },
  { value: 'chase', label: 'Chase' },
  { value: 'wells_fargo', label: 'Wells Fargo' },
  { value: 'schwab', label: 'Charles Schwab' },
  { value: 'amex', label: 'American Express' },
  { value: 'citi', label: 'Citi' },
]

const ACCOUNT_TYPES = [
  { value: 'checking', label: 'Cuenta Corriente' },
  { value: 'savings', label: 'Cuenta Ahorro' },
  { value: 'credit_card', label: 'Tarjeta de Crédito' },
  { value: 'digital_wallet', label: 'Billetera Digital' },
]

const ACCOUNT_TYPE_ICONS: Record<string, string> = {
  checking: '🏦',
  savings: '💰',
  credit_card: '💳',
  digital_wallet: '📱',
}

export default function Accounts() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [bank, setBank] = useState('banco_chile')
  const [accountType, setAccountType] = useState('checking')
  const [currency, setCurrency] = useState('CLP')

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.list,
  })

  const mutation = useMutation({
    mutationFn: () =>
      accountsApi.create({ name, bank, account_type: accountType, currency }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      setShowForm(false)
      setName('')
      setBank('banco_chile')
      setAccountType('checking')
      setCurrency('CLP')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    mutation.mutate()
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cuentas</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gestiona tus cuentas bancarias y tarjetas
          </p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <span>+</span>
            <span>Nueva Cuenta</span>
          </button>
        )}
      </div>

      {/* Formulario nueva cuenta */}
      {showForm && (
        <div className="bg-white rounded-xl border border-blue-200 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">Nueva Cuenta</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Nombre *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ej: BCI Cuenta Vista, Visa Santander..."
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Banco *
                </label>
                <select
                  value={bank}
                  onChange={(e) => setBank(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  {BANKS.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Tipo *
                </label>
                <select
                  value={accountType}
                  onChange={(e) => setAccountType(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  {ACCOUNT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">
                Moneda *
              </label>
              <div className="flex gap-2">
                {['CLP', 'USD'].map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setCurrency(c)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                      currency === c
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    {c === 'CLP' ? '🇨🇱 CLP' : '🇺🇸 USD'}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                type="submit"
                disabled={mutation.isPending || !name.trim()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium py-2 rounded-lg transition-colors"
              >
                {mutation.isPending ? 'Guardando...' : 'Guardar Cuenta'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium py-2 rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>

            {mutation.isError && (
              <p className="text-xs text-red-600">
                Error al guardar la cuenta. Inténtalo de nuevo.
              </p>
            )}
          </form>
        </div>
      )}

      {/* Lista de cuentas */}
      {isLoading ? (
        <div className="text-sm text-gray-500 text-center py-8">Cargando cuentas...</div>
      ) : accounts.length === 0 && !showForm ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center space-y-3">
          <div className="text-4xl">🏦</div>
          <p className="text-gray-700 font-medium">No tienes cuentas registradas</p>
          <p className="text-sm text-gray-500">
            Agrega tu primera cuenta para empezar a subir cartolas
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
          >
            + Nueva Cuenta
          </button>
        </div>
      ) : accounts.length > 0 ? (
        <div className="space-y-3">
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4"
            >
              <div className="text-2xl">
                {ACCOUNT_TYPE_ICONS[acc.account_type] ?? '🏦'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {acc.name}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {BANKS.find((b) => b.value === acc.bank)?.label ?? acc.bank}
                  {' · '}
                  {ACCOUNT_TYPES.find((t) => t.value === acc.account_type)?.label ?? acc.account_type}
                </p>
              </div>
              <span
                className={`text-xs font-bold px-2 py-1 rounded-full ${
                  acc.currency === 'USD'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {acc.currency}
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
