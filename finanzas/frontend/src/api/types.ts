export type TransactionType = 'income' | 'expense' | 'transfer'

export interface Account {
  id: string
  name: string
  bank: string
  account_type: string
  currency: string
  created_at: string
}

export interface Category {
  id: string
  name: string
  slug: string
  icon: string
  color: string
  is_income: boolean
  sort_order: number
}

export interface Transaction {
  id: string
  account_id: string
  date: string
  description: string
  amount: number
  currency: string
  transaction_type: TransactionType
  category_id: string | null
  category_name: string | null
  category_slug: string | null
  category_icon: string | null
  category_color: string | null
  is_auto_categorized: boolean
  is_duplicate: boolean
  month: number
  year: number
  source_file: string | null
  notes: string | null
  created_at: string
}

export interface PaginatedTransactions {
  items: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CategoryBreakdown {
  category_id: string | null
  category_name: string
  category_slug: string
  icon: string
  color: string
  amount: number
  count: number
  pct_of_total: number
}

export interface MonthlySummary {
  year: number
  month: number
  total_income: number
  total_expense: number
  net: number
  by_category: CategoryBreakdown[]
  transaction_count: number
}

export interface MonthComparison {
  year: number
  month: number
  total_income: number
  total_expense: number
  net: number
  by_category: Record<string, number>
}

export interface BudgetStatus {
  category_id: string
  category_name: string
  category_slug: string
  icon: string
  color: string
  budget_amount: number
  actual_amount: number
  remaining: number
  pct_used: number
}

export interface UploadResponse {
  upload_log_id: string | null
  total_parsed: number
  inserted: number
  duplicates: number
  errors: string[]
  bank_detected: string | null
  parser_used: string | null
}

export interface TransactionFilters {
  year?: number
  month?: number
  account_id?: string
  category_id?: string
  transaction_type?: TransactionType
  include_duplicates?: boolean
  search?: string
  page?: number
  page_size?: number
}
