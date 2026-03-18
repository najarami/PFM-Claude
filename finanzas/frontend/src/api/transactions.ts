import { api } from './client'
import type { PaginatedTransactions, Transaction, TransactionFilters } from './types'

function buildQuery(filters: TransactionFilters): string {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      params.append(k, String(v))
    }
  })
  const q = params.toString()
  return q ? `?${q}` : ''
}

export const transactionsApi = {
  list: (filters: TransactionFilters = {}) =>
    api.get<PaginatedTransactions>(`/api/transactions${buildQuery(filters)}`),
  updateCategory: (id: string, categoryId: string | null) =>
    api.patch<Transaction>(`/api/transactions/${id}/category`, { category_id: categoryId }),
  updateNotes: (id: string, notes: string) =>
    api.patch<Transaction>(`/api/transactions/${id}/notes`, { notes }),
}
