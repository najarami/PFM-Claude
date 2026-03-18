import { api } from './client'
import type { Account } from './types'

export const accountsApi = {
  list: () => api.get<Account[]>('/api/accounts'),
  create: (data: { name: string; bank: string; account_type: string; currency?: string }) =>
    api.post<Account>('/api/accounts', data),
}
