import { api } from './client'
import type { BudgetStatus } from './types'

export const budgetApi = {
  list: (year: number, month: number, currency = 'CLP') =>
    api.get<BudgetStatus[]>(`/api/budget?year=${year}&month=${month}&currency=${currency}`),
  set: (categorySlug: string, amount: number, month = 0, year = 0, currency = 'CLP') =>
    api.put(`/api/budget/${categorySlug}`, { amount, month, year, currency }),
}
