import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import MonthlyView from './pages/MonthlyView'
import Comparison from './pages/Comparison'
import BudgetSettings from './pages/BudgetSettings'
import Upload from './pages/Upload'
import Accounts from './pages/Accounts'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/monthly" element={<MonthlyView />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/budget" element={<BudgetSettings />} />
          <Route path="/accounts" element={<Accounts />} />
          <Route path="/upload" element={<Upload />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
