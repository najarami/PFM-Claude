import { create } from 'zustand'

export type Currency = 'CLP' | 'USD'
export type ViewMode = 'native' | 'converted'

interface MonthStore {
  year: number
  month: number
  currency: Currency
  viewMode: ViewMode
  setMonth: (year: number, month: number) => void
  setCurrency: (currency: Currency) => void
  setViewMode: (mode: ViewMode) => void
}

const now = new Date()

export const useMonthStore = create<MonthStore>((set) => ({
  year: now.getFullYear(),
  month: now.getMonth() + 1,
  currency: 'CLP',
  viewMode: 'native',
  setMonth: (year, month) => set({ year, month }),
  setCurrency: (currency) => set({ currency }),
  setViewMode: (viewMode) => set({ viewMode }),
}))
