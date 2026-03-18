import { api } from './client'
import type { MonthComparison, MonthlySummary } from './types'

export const summaryApi = {
  monthly: (year: number, month: number, currency = 'CLP', mode = 'native') =>
    api.get<MonthlySummary>(`/api/summary/${year}/${month}?currency=${currency}&mode=${mode}`),
  comparison: (months: Array<{ year: number; month: number }>, currency = 'CLP', mode = 'native') => {
    const params = months.map(m => `months=${m.year}-${String(m.month).padStart(2, '0')}`).join('&')
    return api.get<MonthComparison[]>(`/api/comparison?${params}&currency=${currency}&mode=${mode}`)
  },
}
