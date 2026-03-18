import { create } from 'zustand'

interface FilterStore {
  accountId: string | undefined
  categoryId: string | undefined
  transactionType: string | undefined
  search: string
  includeDuplicates: boolean
  setFilters: (filters: Partial<Omit<FilterStore, 'setFilters' | 'resetFilters'>>) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterStore>((set) => ({
  accountId: undefined,
  categoryId: undefined,
  transactionType: undefined,
  search: '',
  includeDuplicates: false,
  setFilters: (filters) => set((s) => ({ ...s, ...filters })),
  resetFilters: () =>
    set({
      accountId: undefined,
      categoryId: undefined,
      transactionType: undefined,
      search: '',
      includeDuplicates: false,
    }),
}))
