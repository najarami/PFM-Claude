import { create } from 'zustand'

export type Currency = 'CLP' | 'USD'

interface MonthStore {
  year: number
  month: number
  currency: Currency
  setMonth: (year: number, month: number) => void
  setCurrency: (currency: Currency) => void
}

const now = new Date()

export const useMonthStore = create<MonthStore>((set) => ({
  year: now.getFullYear(),
  month: now.getMonth() + 1,
  currency: 'CLP',
  setMonth: (year, month) => set({ year, month }),
  setCurrency: (currency) => set({ currency }),
}))
